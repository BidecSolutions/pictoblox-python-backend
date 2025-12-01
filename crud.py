"""
CRUD Operations for Database Models
Create, Read, Update, Delete functions
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
import models
import schemas
from auth import get_password_hash
from datetime import datetime


# ============================================================================
# USER CRUD
# ============================================================================

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user"""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> models.User:
    """Update user profile"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get list of users"""
    return db.query(models.User).offset(skip).limit(limit).all()


# ============================================================================
# PROJECT CRUD
# ============================================================================

def create_project(db: Session, project: schemas.ProjectCreate, user_id: int) -> models.Project:
    """Create a new project"""
    db_project = models.Project(
        **project.dict(),
        user_id=user_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    """Get project by ID"""
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_user_projects(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Project]:
    """Get all projects for a user"""
    return db.query(models.Project)\
        .filter(models.Project.user_id == user_id)\
        .order_by(models.Project.updated_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def update_project(
    db: Session, 
    project_id: int, 
    project_update: schemas.ProjectUpdate
) -> models.Project:
    """Update a project"""
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    # Increment version if workspace changed
    if 'workspace_xml' in update_data or 'workspace_json' in update_data:
        db_project.version += 1
    
    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """Delete a project"""
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True


def duplicate_project(db: Session, project_id: int, user_id: int) -> models.Project:
    """Duplicate/clone a project"""
    original = get_project(db, project_id)
    if not original:
        return None
    
    # Create new project with copied data
    new_project = models.Project(
        title=f"{original.title} (Copy)",
        description=original.description,
        user_id=user_id,
        workspace_xml=original.workspace_xml,
        workspace_json=original.workspace_json,
        generated_code=original.generated_code,
        code_language=original.code_language,
        parent_project_id=original.id,
        is_public=False,  # Clones start as private
        status=models.ProjectStatus.DRAFT
    )
    
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    # Update fork count of original
    original.fork_count += 1
    db.commit()
    
    # Copy assets
    for asset in original.assets:
        new_asset = models.Asset(
            project_id=new_project.id,
            name=asset.name,
            asset_type=asset.asset_type,
            file_url=asset.file_url,
            data_base64=asset.data_base64,
            mime_type=asset.mime_type,
            properties=asset.properties,
            width=asset.width,
            height=asset.height,
            duration=asset.duration
        )
        db.add(new_asset)
    
    db.commit()
    db.refresh(new_project)
    return new_project


def get_public_projects(
    db: Session, 
    skip: int = 0, 
    limit: int = 50
) -> List[models.Project]:
    """Get all public projects"""
    return db.query(models.Project)\
        .filter(
            and_(
                models.Project.is_public == True,
                models.Project.status == models.ProjectStatus.PUBLISHED
            )
        )\
        .order_by(models.Project.view_count.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def increment_project_views(db: Session, project_id: int) -> bool:
    """Increment project view count"""
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db_project.view_count += 1
    db.commit()
    return True


# ============================================================================
# ASSET CRUD
# ============================================================================

def create_asset(db: Session, asset: schemas.AssetCreate, project_id: int) -> models.Asset:
    """Create a new asset"""
    db_asset = models.Asset(
        **asset.dict(),
        project_id=project_id
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


def get_asset(db: Session, asset_id: int) -> Optional[models.Asset]:
    """Get asset by ID"""
    return db.query(models.Asset).filter(models.Asset.id == asset_id).first()


def get_project_assets(db: Session, project_id: int) -> List[models.Asset]:
    """Get all assets for a project"""
    return db.query(models.Asset)\
        .filter(models.Asset.project_id == project_id)\
        .order_by(models.Asset.created_at.desc())\
        .all()


def delete_asset(db: Session, asset_id: int) -> bool:
    """Delete an asset"""
    db_asset = get_asset(db, asset_id)
    if not db_asset:
        return False
    
    db.delete(db_asset)
    db.commit()
    return True


# ============================================================================
# EXECUTION LOG CRUD
# ============================================================================

def create_execution_log(
    db: Session,
    user_id: int,
    project_id: Optional[int],
    code: str,
    language: str,
    output: Optional[str],
    error: Optional[str],
    execution_time: float
) -> models.ExecutionLog:
    """Create execution log entry"""
    db_log = models.ExecutionLog(
        user_id=user_id,
        project_id=project_id,
        code=code,
        language=language,
        output=output,
        error=error,
        execution_time=execution_time,
        exit_code=0 if not error else 1
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_user_execution_logs(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[models.ExecutionLog]:
    """Get execution logs for a user"""
    return db.query(models.ExecutionLog)\
        .filter(models.ExecutionLog.user_id == user_id)\
        .order_by(models.ExecutionLog.executed_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


def get_project_execution_logs(
    db: Session,
    project_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[models.ExecutionLog]:
    """Get execution logs for a project"""
    return db.query(models.ExecutionLog)\
        .filter(models.ExecutionLog.project_id == project_id)\
        .order_by(models.ExecutionLog.executed_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()


# ============================================================================
# PROJECT SHARING CRUD
# ============================================================================

def share_project(
    db: Session,
    project_id: int,
    share_with_user_id: int,
    can_edit: bool = False
) -> models.ProjectShare:
    """Share a project with another user"""
    # Check if already shared
    existing = db.query(models.ProjectShare).filter(
        and_(
            models.ProjectShare.project_id == project_id,
            models.ProjectShare.shared_with_user_id == share_with_user_id
        )
    ).first()
    
    if existing:
        existing.can_edit = can_edit
        db.commit()
        db.refresh(existing)
        return existing
    
    db_share = models.ProjectShare(
        project_id=project_id,
        shared_with_user_id=share_with_user_id,
        can_edit=can_edit
    )
    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def get_shared_projects(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100
) -> List[models.Project]:
    """Get projects shared with a user"""
    return db.query(models.Project)\
        .join(models.ProjectShare)\
        .filter(models.ProjectShare.shared_with_user_id == user_id)\
        .offset(skip)\
        .limit(limit)\
        .all()


def unshare_project(db: Session, project_id: int, user_id: int) -> bool:
    """Remove project sharing"""
    share = db.query(models.ProjectShare).filter(
        and_(
            models.ProjectShare.project_id == project_id,
            models.ProjectShare.shared_with_user_id == user_id
        )
    ).first()
    
    if not share:
        return False
    
    db.delete(share)
    db.commit()
    return True


# ============================================================================
# EXTENSION CRUD
# ============================================================================

def create_extension(db: Session, extension: schemas.ExtensionCreate) -> models.Extension:
    """Create a new extension"""
    db_extension = models.Extension(**extension.dict())
    db.add(db_extension)
    db.commit()
    db.refresh(db_extension)
    return db_extension


def get_extension(db: Session, extension_id: int) -> Optional[models.Extension]:
    """Get extension by ID"""
    return db.query(models.Extension).filter(models.Extension.id == extension_id).first()


def get_extensions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True
) -> List[models.Extension]:
    """Get all extensions"""
    query = db.query(models.Extension)
    
    if active_only:
        query = query.filter(models.Extension.is_active == True)
    
    return query.offset(skip).limit(limit).all()


def get_extensions_by_category(
    db: Session,
    category: str
) -> List[models.Extension]:
    """Get extensions by category"""
    return db.query(models.Extension)\
        .filter(
            and_(
                models.Extension.category == category,
                models.Extension.is_active == True
            )
        )\
        .all()



"""
Add these CRUD operations to your existing crud.py file
Append after your existing CRUD functions
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict, Any
import models
import schemas
from datetime import datetime


# ============================================================================
# SPRITE CRUD OPERATIONS
# ============================================================================

def create_sprite(db: Session, sprite: schemas.SpriteCreate) -> models.Sprite:
    """Create a new sprite"""
    # Get max layer_order for this project
    max_layer = db.query(func.max(models.Sprite.layer_order))\
        .filter(models.Sprite.project_id == sprite.project_id)\
        .scalar() or -1
    
    sprite_data = sprite.dict()
    sprite_data['layer_order'] = max_layer + 1  # Put new sprite on top
    
    db_sprite = models.Sprite(**sprite_data)
    db.add(db_sprite)
    db.commit()
    db.refresh(db_sprite)
    return db_sprite


def get_sprite(
    db: Session, 
    sprite_id: int, 
    include_costumes: bool = False,
    include_variables: bool = False,
    include_lists: bool = False
) -> Optional[models.Sprite]:
    """Get sprite by ID with optional related data"""
    query = db.query(models.Sprite)
    
    if include_costumes:
        query = query.options(joinedload(models.Sprite.costumes))
    if include_variables:
        query = query.options(joinedload(models.Sprite.variables))
    if include_lists:
        query = query.options(joinedload(models.Sprite.lists))
    
    return query.filter(models.Sprite.id == sprite_id).first()


def get_project_sprites(
    db: Session, 
    project_id: int,
    include_costumes: bool = False
) -> List[models.Sprite]:
    """Get all sprites for a project, ordered by layer"""
    query = db.query(models.Sprite)\
        .filter(models.Sprite.project_id == project_id)
    
    if include_costumes:
        query = query.options(joinedload(models.Sprite.costumes))
    
    return query.order_by(models.Sprite.layer_order).all()


def update_sprite(
    db: Session, 
    sprite_id: int, 
    sprite_update: schemas.SpriteUpdate
) -> Optional[models.Sprite]:
    """Update a sprite"""
    db_sprite = get_sprite(db, sprite_id)
    if not db_sprite:
        return None
    
    update_data = sprite_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sprite, field, value)
    
    db.commit()
    db.refresh(db_sprite)
    return db_sprite


def delete_sprite(db: Session, sprite_id: int) -> bool:
    """Delete a sprite"""
    db_sprite = get_sprite(db, sprite_id)
    if not db_sprite:
        return False
    
    db.delete(db_sprite)
    db.commit()
    return True


def duplicate_sprite(
    db: Session, 
    sprite_id: int, 
    new_name: Optional[str] = None
) -> Optional[models.Sprite]:
    """Duplicate/clone a sprite with all its costumes"""
    original = get_sprite(db, sprite_id, include_costumes=True)
    if not original:
        return None
    
    # Create new sprite
    new_sprite_data = {
        'project_id': original.project_id,
        'name': new_name or f"{original.name} (copy)",
        'x_position': original.x_position + 20,  # Offset position
        'y_position': original.y_position + 20,
        'direction': original.direction,
        'size': original.size,
        'is_visible': original.is_visible,
        'rotation_style': original.rotation_style,
        'draggable': original.draggable,
        'properties': original.properties.copy() if original.properties else {}
    }
    
    new_sprite = models.Sprite(**new_sprite_data)
    db.add(new_sprite)
    db.flush()  # Get sprite ID
    
    # Clone costumes
    for costume in original.costumes:
        new_costume = models.Costume(
            sprite_id=new_sprite.id,
            name=costume.name,
            image_url=costume.image_url,
            image_data=costume.image_data,
            mime_type=costume.mime_type,
            width=costume.width,
            height=costume.height,
            center_x=costume.center_x,
            center_y=costume.center_y,
            bitmap_resolution=costume.bitmap_resolution,
            costume_order=costume.costume_order
        )
        db.add(new_costume)
    
    db.commit()
    db.refresh(new_sprite)
    return new_sprite


def reorder_sprite_layers(
    db: Session, 
    project_id: int, 
    sprite_orders: List[Dict[str, int]]
) -> bool:
    """Update layer order for multiple sprites"""
    try:
        for item in sprite_orders:
            sprite_id = item.get('sprite_id')
            layer_order = item.get('layer_order')
            
            if sprite_id and layer_order is not None:
                sprite = get_sprite(db, sprite_id)
                if sprite and sprite.project_id == project_id:
                    sprite.layer_order = layer_order
        
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def bring_sprite_to_front(db: Session, sprite_id: int) -> Optional[models.Sprite]:
    """Bring sprite to front (highest layer)"""
    sprite = get_sprite(db, sprite_id)
    if not sprite:
        return None
    
    max_layer = db.query(func.max(models.Sprite.layer_order))\
        .filter(models.Sprite.project_id == sprite.project_id)\
        .scalar() or 0
    
    sprite.layer_order = max_layer + 1
    db.commit()
    db.refresh(sprite)
    return sprite


def send_sprite_to_back(db: Session, sprite_id: int) -> Optional[models.Sprite]:
    """Send sprite to back (lowest layer)"""
    sprite = get_sprite(db, sprite_id)
    if not sprite:
        return None
    
    # Shift all sprites up
    sprites = get_project_sprites(db, sprite.project_id)
    for s in sprites:
        if s.id != sprite_id:
            s.layer_order += 1
    
    sprite.layer_order = 0
    db.commit()
    db.refresh(sprite)
    return sprite


# crud.py

from sqlalchemy.orm import Session
import models
import schemas
import math
from typing import Optional

# --- Configuration Constants (Define these at the top of crud.py) ---
# Assuming a standard Scratch/PictoBlox stage size
STAGE_WIDTH = 480 
STAGE_HEIGHT = 360 
X_MIN = -STAGE_WIDTH / 2 # -240
X_MAX = STAGE_WIDTH / 2  # 240
Y_MIN = -STAGE_HEIGHT / 2 # -180
Y_MAX = STAGE_HEIGHT / 2 # 180


# --- Helper Function for Getting Sprite ---

# def get_sprite(db: Session, sprite_id: int):
#     """Retrieve a sprite by ID."""
#     return db.query(models.Sprite).filter(models.Sprite.id == sprite_id).first()


# --- Motion Block Implementation ---

def move_sprite(db: Session, sprite_id: int, steps: float) -> Optional[models.Sprite]:
    """Move the sprite 'steps' steps in its current direction."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    # Scratch directions: 90 is right, 0 is up, -90/270 is left, 180 is down.
    # Convert direction to standard radians (0=right, 90=up)
    direction_rad = math.radians(90 - sprite.direction) 
    
    delta_x = steps * math.cos(direction_rad)
    delta_y = steps * math.sin(direction_rad)
    
    sprite.x_position += delta_x
    sprite.y_position += delta_y
    
    db.commit()
    db.refresh(sprite)
    return sprite


def turn_sprite(db: Session, sprite_id: int, degrees: float, clockwise: bool) -> Optional[models.Sprite]:
    """Turn the sprite by 'degrees' (clockwise or counter-clockwise)."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    if clockwise:
        sprite.direction = (sprite.direction + degrees) % 360
    else:
        sprite.direction = (sprite.direction - degrees) % 360
        
    # Normalize direction to be between -180 and 180 if preferred, though 0-360 is fine.
    if sprite.direction > 180:
        sprite.direction -= 360
    elif sprite.direction <= -180:
        sprite.direction += 360

    db.commit()
    db.refresh(sprite)
    return sprite


def go_to_position(db: Session, sprite_id: int, target: schemas.MotionTarget, x: Optional[float], y: Optional[float]) -> Optional[models.Sprite]:
    """Go to a specific x/y, random position, or target object."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    if target == schemas.MotionTarget.RANDOM_POSITION:
        import random
        # Moves to a random position within stage boundaries
        sprite.x_position = random.uniform(X_MIN, X_MAX)
        sprite.y_position = random.uniform(Y_MIN, Y_MAX)
    
    elif target == schemas.MotionTarget.MOUSE_POINTER:
        # NOTE: For a REST API, the client must provide the mouse coordinates as x and y.
        if x is not None and y is not None:
            sprite.x_position = x
            sprite.y_position = y
        else:
            # Cannot move to mouse-pointer without client data
            raise ValueError("Mouse coordinates not provided for target.")
            
    else: # Go to x: y: block
        if x is not None: 
            sprite.x_position = x
        if y is not None: 
            sprite.y_position = y
    
    db.commit()
    db.refresh(sprite)
    return sprite


def glide_to_position(db: Session, sprite_id: int, secs: float, target: Optional[schemas.MotionTarget], x: Optional[float], y: Optional[float]) -> Optional[models.Sprite]:
    """
    Update sprite position to the target. 
    In a REST API, this action is instantaneous server-side. The client handles the animation over 'secs'.
    """
    # This function uses the same logic as go_to_position to determine the final coordinate.
    # The 'secs' parameter is informational for the client but does not affect the DB update time.
    return go_to_position(db, sprite_id, target=target, x=x, y=y)


def set_sprite_direction(db: Session, sprite_id: int, direction: float) -> Optional[models.Sprite]:
    """Set the sprite's direction."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.direction = direction % 360
    db.commit()
    db.refresh(sprite)
    return sprite


def point_sprite_towards(db: Session, sprite_id: int, target: schemas.MotionPointTowardsTarget, x: Optional[float], y: Optional[float]) -> Optional[models.Sprite]:
    """Point the sprite towards a target (mouse-pointer or another sprite)."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    target_x = 0.0
    target_y = 0.0
    
    if target == schemas.MotionTarget.MOUSE_POINTER:
        # Requires client to send mouse coordinates
        if x is not None and y is not None:
            target_x = x
            target_y = y
        else:
            raise ValueError("Mouse coordinates not provided for target.")
    # Add logic here for pointing towards another sprite ID if you implement that target type.
    
    # Calculate direction using atan2: angle = atan2(y2-y1, x2-x1)
    # Note: Scratch direction is 90 degrees offset (90 is up, 0 is right in standard math)
    angle_rad = math.atan2(target_y - sprite.y_position, target_x - sprite.x_position)
    
    # Convert from standard math radians to Scratch degrees
    angle_deg = math.degrees(angle_rad)
    scratch_direction = 90 - angle_deg 
    
    sprite.direction = scratch_direction % 360
    
    db.commit()
    db.refresh(sprite)
    return sprite


def change_sprite_x(db: Session, sprite_id: int, change: float) -> Optional[models.Sprite]:
    """Change the sprite's x position by an amount."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.x_position += change
    
    db.commit()
    db.refresh(sprite)
    return sprite


def set_sprite_x(db: Session, sprite_id: int, value: float) -> Optional[models.Sprite]:
    """Set the sprite's x position to a specific value."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.x_position = value
    
    db.commit()
    db.refresh(sprite)
    return sprite


def change_sprite_y(db: Session, sprite_id: int, change: float) -> Optional[models.Sprite]:
    """Change the sprite's y position by an amount."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.y_position += change
    
    db.commit()
    db.refresh(sprite)
    return sprite


def set_sprite_y(db: Session, sprite_id: int, value: float) -> Optional[models.Sprite]:
    """Set the sprite's y position to a specific value."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.y_position = value
    
    db.commit()
    db.refresh(sprite)
    return sprite


def if_on_edge_bounce(db: Session, sprite_id: int) -> Optional[models.Sprite]:
    """If the sprite is touching the edge of the stage, reverse its direction."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None

    x = sprite.x_position
    y = sprite.y_position
    direction = sprite.direction
    
    # Simple check if sprite center is beyond boundary
    if x > X_MAX or x < X_MIN:
        # Bounce on X axis (reflect direction across Y-axis, i.e., 180 - direction)
        direction = 180 - direction
        
        # Move back inside boundary slightly to prevent immediate re-bounce
        if x > X_MAX:
            sprite.x_position = X_MAX - 1.0 
        else:
            sprite.x_position = X_MIN + 1.0

    elif y > Y_MAX or y < Y_MIN:
        # Bounce on Y axis (reflect direction across X-axis, i.e., 360 - direction or -direction)
        direction = 360 - direction
        
        # Move back inside boundary slightly
        if y > Y_MAX:
            sprite.y_position = Y_MAX - 1.0
        else:
            sprite.y_position = Y_MIN + 1.0
            
    # Apply rotation style logic after calculating the new direction
    if sprite.rotation_style == models.RotationStyle.LEFT_RIGHT:
        if direction > 90 and direction <= 270:
            # Sprite should face left (Flip costume horizontally on the client)
            # Direction remains the same, but the costume displays mirrored.
            pass
        else:
            # Sprite should face right
            pass
    elif sprite.rotation_style == models.RotationStyle.DONT_ROTATE:
        # Costume never rotates on the client
        direction = sprite.direction # Do not update direction based on bounce calculation if DONT_ROTATE
        
    sprite.direction = direction % 360 # Save the new direction

    db.commit()
    db.refresh(sprite)
    return sprite


def set_sprite_rotation_style(db: Session, sprite_id: int, rotation_style: schemas.RotationStyle) -> Optional[models.Sprite]:
    """Set the sprite's rotation style."""
    sprite = get_sprite(db, sprite_id)
    if not sprite: return None
    
    sprite.rotation_style = rotation_style
    
    db.commit()
    db.refresh(sprite)
    return sprite


# ============================================================================
# COSTUME CRUD OPERATIONS
# ============================================================================

def create_costume(db: Session, costume: schemas.CostumeCreate) -> models.Costume:
    """Create a new costume"""
    db_costume = models.Costume(**costume.dict())
    db.add(db_costume)
    db.commit()
    db.refresh(db_costume)
    return db_costume


def get_costume(db: Session, costume_id: int) -> Optional[models.Costume]:
    """Get costume by ID"""
    return db.query(models.Costume).filter(models.Costume.id == costume_id).first()


def get_sprite_costumes(db: Session, sprite_id: int) -> List[models.Costume]:
    """Get all costumes for a sprite"""
    return db.query(models.Costume)\
        .filter(models.Costume.sprite_id == sprite_id)\
        .order_by(models.Costume.costume_order)\
        .all()


def update_costume(
    db: Session, 
    costume_id: int, 
    costume_update: schemas.CostumeUpdate
) -> Optional[models.Costume]:
    """Update a costume"""
    db_costume = get_costume(db, costume_id)
    if not db_costume:
        return None
    
    update_data = costume_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_costume, field, value)
    
    db.commit()
    db.refresh(db_costume)
    return db_costume


def delete_costume(db: Session, costume_id: int) -> bool:
    """Delete a costume"""
    db_costume = get_costume(db, costume_id)
    if not db_costume:
        return False
    
    db.delete(db_costume)
    db.commit()
    return True


def set_sprite_costume(db: Session, sprite_id: int, costume_id: int) -> Optional[models.Sprite]:
    """Set the active costume for a sprite"""
    sprite = get_sprite(db, sprite_id)
    if not sprite:
        return None
    
    # Verify costume belongs to this sprite
    costume = get_costume(db, costume_id)
    if not costume or costume.sprite_id != sprite_id:
        return None
    
    sprite.current_costume_id = costume_id
    db.commit()
    db.refresh(sprite)
    return sprite


def duplicate_costume(
    db: Session, 
    costume_id: int, 
    new_name: Optional[str] = None
) -> Optional[models.Costume]:
    """Duplicate a costume"""
    original = get_costume(db, costume_id)
    if not original:
        return None
    
    new_costume = models.Costume(
        sprite_id=original.sprite_id,
        name=new_name or f"{original.name} (copy)",
        image_url=original.image_url,
        image_data=original.image_data,
        mime_type=original.mime_type,
        width=original.width,
        height=original.height,
        center_x=original.center_x,
        center_y=original.center_y,
        bitmap_resolution=original.bitmap_resolution,
        costume_order=original.costume_order + 1
    )
    
    db.add(new_costume)
    db.commit()
    db.refresh(new_costume)
    return new_costume


# ============================================================================
# BACKDROP CRUD OPERATIONS
# ============================================================================

def create_backdrop(db: Session, backdrop: schemas.BackdropCreate) -> models.Backdrop:
    """Create a new backdrop"""
    db_backdrop = models.Backdrop(**backdrop.dict())
    db.add(db_backdrop)
    db.commit()
    db.refresh(db_backdrop)
    return db_backdrop


def get_backdrop(db: Session, backdrop_id: int) -> Optional[models.Backdrop]:
    """Get backdrop by ID"""
    return db.query(models.Backdrop).filter(models.Backdrop.id == backdrop_id).first()


def get_project_backdrops(db: Session, project_id: int) -> List[models.Backdrop]:
    """Get all backdrops for a project"""
    return db.query(models.Backdrop)\
        .filter(models.Backdrop.project_id == project_id)\
        .order_by(models.Backdrop.backdrop_order)\
        .all()


def update_backdrop(
    db: Session, 
    backdrop_id: int, 
    backdrop_update: schemas.BackdropUpdate
) -> Optional[models.Backdrop]:
    """Update a backdrop"""
    db_backdrop = get_backdrop(db, backdrop_id)
    if not db_backdrop:
        return None
    
    update_data = backdrop_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_backdrop, field, value)
    
    db.commit()
    db.refresh(db_backdrop)
    return db_backdrop


def delete_backdrop(db: Session, backdrop_id: int) -> bool:
    """Delete a backdrop"""
    db_backdrop = get_backdrop(db, backdrop_id)
    if not db_backdrop:
        return False
    
    db.delete(db_backdrop)
    db.commit()
    return True


# ============================================================================
# STAGE SETTINGS CRUD OPERATIONS
# ============================================================================

def create_stage_setting(db: Session, settings: schemas.StageSettingCreate) -> models.StageSetting:
    """Create stage settings"""
    db_settings = models.StageSetting(**settings.dict())
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings


def get_stage_setting(db: Session, project_id: int) -> Optional[models.StageSetting]:
    """Get stage settings for a project"""
    return db.query(models.StageSetting)\
        .filter(models.StageSetting.project_id == project_id)\
        .first()


def update_stage_setting(
    db: Session, 
    project_id: int, 
    settings_update: schemas.StageSettingUpdate
) -> Optional[models.StageSetting]:
    """Update or create stage settings"""
    db_settings = get_stage_setting(db, project_id)
    
    if db_settings:
        # Update existing
        update_data = settings_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_settings, field, value)
    else:
        # Create new
        settings_data = settings_update.dict(exclude_unset=True)
        settings_data['project_id'] = project_id
        db_settings = models.StageSetting(**settings_data)
        db.add(db_settings)
    
    db.commit()
    db.refresh(db_settings)
    return db_settings


def set_stage_backdrop(
    db: Session, 
    project_id: int, 
    backdrop_id: int
) -> Optional[models.StageSetting]:
    """Set the active backdrop for stage"""
    settings = get_stage_setting(db, project_id)
    if not settings:
        # Create default settings
        settings = create_stage_setting(db, schemas.StageSettingCreate(
            project_id=project_id,
            current_backdrop_id=backdrop_id
        ))
    else:
        settings.current_backdrop_id = backdrop_id
        db.commit()
        db.refresh(settings)
    
    return settings


def get_complete_stage_data(db: Session, project_id: int) -> Dict[str, Any]:
    """Get complete stage data (settings, sprites, backdrops)"""
    stage_settings = get_stage_setting(db, project_id)
    sprites = get_project_sprites(db, project_id, include_costumes=True)
    backdrops = get_project_backdrops(db, project_id)
    current_backdrop = None
    
    if stage_settings and stage_settings.current_backdrop_id:
        current_backdrop = get_backdrop(db, stage_settings.current_backdrop_id)
    
    return {
        'stage_settings': stage_settings,
        'current_backdrop': current_backdrop,
        'sprites': sprites,
        'backdrops': backdrops
    }


# ============================================================================
# SPRITE VARIABLE CRUD OPERATIONS
# ============================================================================

def create_variable(db: Session, variable: schemas.SpriteVariableCreate) -> models.SpriteVariable:
    """Create a variable (global or sprite-specific)"""
    db_variable = models.SpriteVariable(**variable.dict())
    db.add(db_variable)
    db.commit()
    db.refresh(db_variable)
    return db_variable


def get_variable(db: Session, variable_id: int) -> Optional[models.SpriteVariable]:
    """Get variable by ID"""
    return db.query(models.SpriteVariable)\
        .filter(models.SpriteVariable.id == variable_id)\
        .first()


def get_project_variables(
    db: Session, 
    project_id: int, 
    sprite_id: Optional[int] = None,
    global_only: bool = False
) -> List[models.SpriteVariable]:
    """Get variables for a project or sprite"""
    query = db.query(models.SpriteVariable)\
        .filter(models.SpriteVariable.project_id == project_id)
    
    if global_only:
        query = query.filter(models.SpriteVariable.sprite_id == None)
    elif sprite_id is not None:
        query = query.filter(
            or_(
                models.SpriteVariable.sprite_id == sprite_id,
                models.SpriteVariable.sprite_id == None
            )
        )
    
    return query.all()


def update_variable(
    db: Session, 
    variable_id: int, 
    variable_update: schemas.SpriteVariableUpdate
) -> Optional[models.SpriteVariable]:
    """Update a variable"""
    db_variable = get_variable(db, variable_id)
    if not db_variable:
        return None
    
    update_data = variable_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_variable, field, value)
    
    db.commit()
    db.refresh(db_variable)
    return db_variable


def delete_variable(db: Session, variable_id: int) -> bool:
    """Delete a variable"""
    db_variable = get_variable(db, variable_id)
    if not db_variable:
        return False
    
    db.delete(db_variable)
    db.commit()
    return True


# ============================================================================
# SPRITE LIST CRUD OPERATIONS
# ============================================================================

def create_list(db: Session, list_data: schemas.SpriteListCreate) -> models.SpriteList:
    """Create a list (global or sprite-specific)"""
    db_list = models.SpriteList(**list_data.dict())
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list


def get_list(db: Session, list_id: int) -> Optional[models.SpriteList]:
    """Get list by ID"""
    return db.query(models.SpriteList).filter(models.SpriteList.id == list_id).first()


def get_project_lists(
    db: Session, 
    project_id: int, 
    sprite_id: Optional[int] = None,
    global_only: bool = False
) -> List[models.SpriteList]:
    """Get lists for a project or sprite"""
    query = db.query(models.SpriteList)\
        .filter(models.SpriteList.project_id == project_id)
    
    if global_only:
        query = query.filter(models.SpriteList.sprite_id == None)
    elif sprite_id is not None:
        query = query.filter(
            or_(
                models.SpriteList.sprite_id == sprite_id,
                models.SpriteList.sprite_id == None
            )
        )
    
    return query.all()


def update_list(
    db: Session, 
    list_id: int, 
    list_update: schemas.SpriteListUpdate
) -> Optional[models.SpriteList]:
    """Update a list"""
    db_list = get_list(db, list_id)
    if not db_list:
        return None
    
    update_data = list_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_list, field, value)
    
    db.commit()
    db.refresh(db_list)
    return db_list


def delete_list(db: Session, list_id: int) -> bool:
    """Delete a list"""
    db_list = get_list(db, list_id)
    if not db_list:
        return False
    
    db.delete(db_list)
    db.commit()
    return True


# ============================================================================
# LIBRARY CRUD OPERATIONS
# ============================================================================

def get_library_sprites(
    db: Session, 
    category: Optional[str] = None, 
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.LibrarySprite]:
    """Get library sprites with filters"""
    query = db.query(models.LibrarySprite).filter(models.LibrarySprite.is_official == True)
    
    if category:
        query = query.filter(models.LibrarySprite.category == category)
    
    if search:
        query = query.filter(
            or_(
                models.LibrarySprite.name.ilike(f'%{search}%'),
                models.LibrarySprite.description.ilike(f'%{search}%')
            )
        )
    
    return query.offset(skip).limit(limit).all()


def get_library_backdrops(
    db: Session, 
    category: Optional[str] = None, 
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.LibraryBackdrop]:
    """Get library backdrops with filters"""
    query = db.query(models.LibraryBackdrop).filter(models.LibraryBackdrop.is_official == True)
    
    if category:
        query = query.filter(models.LibraryBackdrop.category == category)
    
    if search:
        query = query.filter(
            or_(
                models.LibraryBackdrop.name.ilike(f'%{search}%'),
                models.LibraryBackdrop.description.ilike(f'%{search}%')
            )
        )
    
    return query.offset(skip).limit(limit).all()


def increment_library_download_count(db: Session, library_sprite_id: int, is_sprite: bool = True):
    """Increment download count for library asset"""
    if is_sprite:
        item = db.query(models.LibrarySprite).filter(models.LibrarySprite.id == library_sprite_id).first()
    else:
        item = db.query(models.LibraryBackdrop).filter(models.LibraryBackdrop.id == library_sprite_id).first()
    
    if item:
        item.download_count += 1
        db.commit()


        