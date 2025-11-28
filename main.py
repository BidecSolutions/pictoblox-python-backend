"""
FastAPI Backend for Blockly-based Visual Programming Platform
Main Application Entry Point
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

import models
import schemas
import crud
import auth
from database import engine, get_db

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blockly Platform API",
    description="Backend API for Visual Programming Platform like PictoBlox",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    return crud.create_user(db=db, user=user)


@app.post("/api/v1/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/users/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user information"""
    return current_user


@app.put("/api/v1/users/me", response_model=schemas.User)
def update_user_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    return crud.update_user(db, current_user.id, user_update)


# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/projects", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(
    project: schemas.ProjectCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    return crud.create_project(db=db, project=project, user_id=current_user.id)


@app.get("/api/v1/projects", response_model=List[schemas.Project])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects for current user"""
    return crud.get_user_projects(db, user_id=current_user.id, skip=skip, limit=limit)


@app.get("/api/v1/projects/{project_id}", response_model=schemas.Project)
def get_project(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific project"""
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    
    return project


@app.put("/api/v1/projects/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a project"""
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this project")
    
    return crud.update_project(db, project_id=project_id, project_update=project_update)


@app.delete("/api/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a project"""
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this project")
    
    crud.delete_project(db, project_id=project_id)
    return None


@app.post("/api/v1/projects/{project_id}/duplicate", response_model=schemas.Project)
def duplicate_project(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate/clone a project"""
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to duplicate this project")
    
    return crud.duplicate_project(db, project_id=project_id, user_id=current_user.id)


# ============================================================================
# CODE EXECUTION ENDPOINTS
# ============================================================================

@app.post("/api/v1/execute", response_model=schemas.ExecutionResult)
def execute_code(
    execution: schemas.CodeExecution,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Execute code in sandbox"""
    from sandbox import execute_python_code
    
    result = execute_python_code(
        code=execution.code,
        language=execution.language,
        timeout=execution.timeout
    )
    
    # Log execution
    crud.create_execution_log(
        db=db,
        user_id=current_user.id,
        project_id=execution.project_id,
        code=execution.code,
        language=execution.language,
        output=result["output"],
        error=result["error"],
        execution_time=result["execution_time"]
    )
    
    return result


# ============================================================================
# ASSET MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/projects/{project_id}/assets", response_model=schemas.Asset)
def upload_asset(
    project_id: int,
    asset: schemas.AssetCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload an asset (sprite, sound, backdrop, etc.)"""
    project = crud.get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.create_asset(db=db, asset=asset, project_id=project_id)


@app.get("/api/v1/projects/{project_id}/assets", response_model=List[schemas.Asset])
def list_assets(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """List all assets for a project"""
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_project_assets(db, project_id=project_id)


@app.delete("/api/v1/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an asset"""
    asset = crud.get_asset(db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    project = crud.get_project(db, project_id=asset.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_asset(db, asset_id=asset_id)
    return None


# ============================================================================
# SHARING & COLLABORATION
# ============================================================================

@app.get("/api/v1/projects/list/public", response_model=List[schemas.Project])
def list_public_projects(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all public projects"""
    return crud.get_public_projects(db, skip=skip, limit=limit)


@app.post("/api/v1/projects/{project_id}/share")
def share_project(
    project_id: int,
    share_data: schemas.ProjectShare,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Share project with other users"""
    project = crud.get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.share_project(db, project_id=project_id, share_with_user_id=share_data.user_id)


"""
Add these API endpoints to your existing main.py file
Append after your existing endpoints (before if __name__ == "__main__")
"""

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
import crud
import auth
from database import get_db
import base64
from io import BytesIO
from PIL import Image


# ============================================================================
# SPRITE MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/sprites", response_model=schemas.Sprite, status_code=status.HTTP_201_CREATED)
def create_sprite(
    sprite: schemas.SpriteCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sprite in a project"""
    # Verify user owns the project
    project = crud.get_project(db, sprite.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this project")
    
    # Check sprite limit (optional)
    existing_sprites = crud.get_project_sprites(db, sprite.project_id)
    if len(existing_sprites) >= 100:  # Max 100 sprites per project
        raise HTTPException(status_code=400, detail="Maximum sprite limit reached")
    
    return crud.create_sprite(db=db, sprite=sprite)


@app.get("/api/v1/projects/{project_id}/sprites", response_model=List[schemas.SpriteWithCostumes])
def list_project_sprites(
    project_id: int,
    include_costumes: bool = Query(True),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sprites for a project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check access rights
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    
    return crud.get_project_sprites(db, project_id=project_id, include_costumes=include_costumes)


@app.get("/api/v1/sprites/{sprite_id}", response_model=schemas.SpriteComplete)
def get_sprite(
    sprite_id: int,
    include_costumes: bool = Query(True),
    include_variables: bool = Query(False),
    include_lists: bool = Query(False),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single sprite with optional related data"""
    sprite = crud.get_sprite(db, sprite_id, include_costumes, include_variables, include_lists)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    # Check access rights
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return sprite


@app.put("/api/v1/sprites/{sprite_id}", response_model=schemas.Sprite)
def update_sprite(
    sprite_id: int,
    sprite_update: schemas.SpriteUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a sprite"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    # Check ownership
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_sprite(db, sprite_id=sprite_id, sprite_update=sprite_update)


@app.delete("/api/v1/sprites/{sprite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sprite(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a sprite"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_sprite(db, sprite_id=sprite_id)
    return None


@app.post("/api/v1/sprites/{sprite_id}/duplicate", response_model=schemas.Sprite)
def duplicate_sprite(
    sprite_id: int,
    new_name: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate/clone a sprite with all costumes"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    duplicated = crud.duplicate_sprite(db, sprite_id, new_name)
    if not duplicated:
        raise HTTPException(status_code=500, detail="Failed to duplicate sprite")
    
    return duplicated


@app.put("/api/v1/projects/{project_id}/sprites/reorder")
def reorder_sprites(
    project_id: int,
    reorder_data: schemas.LayerReorderRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reorder sprite layers (z-index)"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = crud.reorder_sprite_layers(db, project_id, reorder_data.sprite_orders)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reorder sprites")
    
    return {"message": "Sprites reordered successfully"}


@app.put("/api/v1/sprites/{sprite_id}/front", response_model=schemas.Sprite)
def bring_to_front(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Bring sprite to front (top layer)"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.bring_sprite_to_front(db, sprite_id)


@app.put("/api/v1/sprites/{sprite_id}/back", response_model=schemas.Sprite)
def send_to_back(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Send sprite to back (bottom layer)"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.send_sprite_to_back(db, sprite_id)


# ============================================================================
# SPRITE ACTION ENDPOINTS (Runtime operations)
# ============================================================================

@app.put("/api/v1/sprites/{sprite_id}/move")
def move_sprite(
    sprite_id: int,
    move_data: schemas.MoveSpriteRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Move sprite to position"""
    sprite_update = schemas.SpriteUpdate(
        x_position=move_data.x_position,
        y_position=move_data.y_position
    )
    updated = crud.update_sprite(db, sprite_id, sprite_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Sprite not found")
    return updated


@app.put("/api/v1/sprites/{sprite_id}/rotate")
def rotate_sprite(
    sprite_id: int,
    rotate_data: schemas.RotateSpriteRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Rotate sprite to direction"""
    sprite_update = schemas.SpriteUpdate(direction=rotate_data.direction)
    updated = crud.update_sprite(db, sprite_id, sprite_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Sprite not found")
    return updated


@app.put("/api/v1/sprites/{sprite_id}/size")
def change_sprite_size(
    sprite_id: int,
    size_data: schemas.SizeSpriteRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change sprite size"""
    sprite_update = schemas.SpriteUpdate(size=size_data.size)
    updated = crud.update_sprite(db, sprite_id, sprite_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Sprite not found")
    return updated


@app.put("/api/v1/sprites/{sprite_id}/visibility")
def set_sprite_visibility(
    sprite_id: int,
    visibility_data: schemas.VisibilityRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Show/hide sprite"""
    sprite_update = schemas.SpriteUpdate(is_visible=visibility_data.is_visible)
    updated = crud.update_sprite(db, sprite_id, sprite_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Sprite not found")
    return updated


# ============================================================================
# COSTUME MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/costumes", response_model=schemas.Costume, status_code=status.HTTP_201_CREATED)
def create_costume(
    costume: schemas.CostumeCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new costume"""
    sprite = crud.get_sprite(db, costume.sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.create_costume(db=db, costume=costume)


@app.post("/api/v1/costumes/upload", response_model=schemas.Costume)
async def upload_costume_image(
    sprite_id: int,
    name: str,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload costume image file"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read and process image
    contents = await file.read()
    
    # Convert to base64
    image_base64 = base64.b64encode(contents).decode('utf-8')
    
    # Get image dimensions
    try:
        img = Image.open(BytesIO(contents))
        width, height = img.size
    except:
        width, height = None, None
    
    # Get next costume order
    existing_costumes = crud.get_sprite_costumes(db, sprite_id)
    costume_order = len(existing_costumes)
    
    # Create costume
    costume_data = schemas.CostumeCreate(
        sprite_id=sprite_id,
        name=name,
        image_data=image_base64,
        mime_type=file.content_type,
        width=width,
        height=height,
        center_x=width // 2 if width else 0,
        center_y=height // 2 if height else 0,
        costume_order=costume_order
    )
    
    return crud.create_costume(db, costume_data)


@app.get("/api/v1/sprites/{sprite_id}/costumes", response_model=List[schemas.Costume])
def list_sprite_costumes(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all costumes for a sprite"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    return crud.get_sprite_costumes(db, sprite_id=sprite_id)


@app.put("/api/v1/costumes/{costume_id}", response_model=schemas.Costume)
def update_costume(
    costume_id: int,
    costume_update: schemas.CostumeUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a costume"""
    costume = crud.get_costume(db, costume_id)
    if not costume:
        raise HTTPException(status_code=404, detail="Costume not found")
    
    sprite = crud.get_sprite(db, costume.sprite_id)
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_costume(db, costume_id=costume_id, costume_update=costume_update)


@app.delete("/api/v1/costumes/{costume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_costume(
    costume_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a costume"""
    costume = crud.get_costume(db, costume_id)
    if not costume:
        raise HTTPException(status_code=404, detail="Costume not found")
    
    sprite = crud.get_sprite(db, costume.sprite_id)
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_costume(db, costume_id=costume_id)
    return None


@app.put("/api/v1/sprites/{sprite_id}/costume", response_model=schemas.Sprite)
def set_active_costume(
    sprite_id: int,
    costume_request: schemas.SetCostumeRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set active costume for sprite"""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated = crud.set_sprite_costume(db, sprite_id, costume_request.costume_id)
    if not updated:
        raise HTTPException(status_code=400, detail="Invalid costume ID")
    
    return updated


@app.post("/api/v1/costumes/{costume_id}/duplicate", response_model=schemas.Costume)
def duplicate_costume(
    costume_id: int,
    new_name: Optional[str] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Duplicate a costume"""
    costume = crud.get_costume(db, costume_id)
    if not costume:
        raise HTTPException(status_code=404, detail="Costume not found")
    
    sprite = crud.get_sprite(db, costume.sprite_id)
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    duplicated = crud.duplicate_costume(db, costume_id, new_name)
    if not duplicated:
        raise HTTPException(status_code=500, detail="Failed to duplicate costume")
    
    return duplicated

"""
CONTINUATION - Add these endpoints after the costume endpoints in main.py
"""

# ============================================================================
# BACKDROP MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/backdrops", response_model=schemas.Backdrop, status_code=status.HTTP_201_CREATED)
def create_backdrop(
    backdrop: schemas.BackdropCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new backdrop"""
    project = crud.get_project(db, backdrop.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.create_backdrop(db=db, backdrop=backdrop)


@app.post("/api/v1/backdrops/upload", response_model=schemas.Backdrop)
async def upload_backdrop_image(
    project_id: int,
    name: str,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload backdrop image file"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Read and process image
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode('utf-8')
    
    # Get image dimensions
    try:
        img = Image.open(BytesIO(contents))
        width, height = img.size
    except:
        width, height = 480, 360
    
    # Get next backdrop order
    existing_backdrops = crud.get_project_backdrops(db, project_id)
    backdrop_order = len(existing_backdrops)
    
    # Create backdrop
    backdrop_data = schemas.BackdropCreate(
        project_id=project_id,
        name=name,
        image_data=image_base64,
        mime_type=file.content_type,
        width=width,
        height=height,
        backdrop_order=backdrop_order
    )
    
    return crud.create_backdrop(db, backdrop_data)


@app.get("/api/v1/projects/{project_id}/backdrops", response_model=List[schemas.Backdrop])
def list_project_backdrops(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all backdrops for a project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_project_backdrops(db, project_id=project_id)


@app.put("/api/v1/backdrops/{backdrop_id}", response_model=schemas.Backdrop)
def update_backdrop(
    backdrop_id: int,
    backdrop_update: schemas.BackdropUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a backdrop"""
    backdrop = crud.get_backdrop(db, backdrop_id)
    if not backdrop:
        raise HTTPException(status_code=404, detail="Backdrop not found")
    
    project = crud.get_project(db, backdrop.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_backdrop(db, backdrop_id=backdrop_id, backdrop_update=backdrop_update)


@app.delete("/api/v1/backdrops/{backdrop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backdrop(
    backdrop_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a backdrop"""
    backdrop = crud.get_backdrop(db, backdrop_id)
    if not backdrop:
        raise HTTPException(status_code=404, detail="Backdrop not found")
    
    project = crud.get_project(db, backdrop.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_backdrop(db, backdrop_id=backdrop_id)
    return None


# ============================================================================
# STAGE MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/projects/{project_id}/stage", response_model=schemas.StageSetting)
def get_stage_settings(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get stage settings for a project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    settings = crud.get_stage_setting(db, project_id)
    if not settings:
        # Create default settings
        settings_data = schemas.StageSettingCreate(project_id=project_id)
        settings = crud.create_stage_setting(db, settings_data)
    
    return settings


@app.put("/api/v1/projects/{project_id}/stage", response_model=schemas.StageSetting)
def update_stage_settings(
    project_id: int,
    settings_update: schemas.StageSettingUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update stage settings"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_stage_setting(db, project_id, settings_update)


@app.put("/api/v1/projects/{project_id}/stage/backdrop", response_model=schemas.StageSetting)
def set_stage_backdrop(
    project_id: int,
    backdrop_request: schemas.SetBackdropRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set active backdrop for stage"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Verify backdrop belongs to project
    backdrop = crud.get_backdrop(db, backdrop_request.backdrop_id)
    if not backdrop or backdrop.project_id != project_id:
        raise HTTPException(status_code=400, detail="Invalid backdrop ID")
    
    return crud.set_stage_backdrop(db, project_id, backdrop_request.backdrop_id)


@app.get("/api/v1/projects/{project_id}/stage/complete", response_model=schemas.StageComplete)
def get_complete_stage_data(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete stage data (settings, sprites, backdrops)"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_complete_stage_data(db, project_id)


# ============================================================================
# SPRITE VARIABLE ENDPOINTS
# ============================================================================

@app.post("/api/v1/variables", response_model=schemas.SpriteVariable, status_code=status.HTTP_201_CREATED)
def create_variable(
    variable: schemas.SpriteVariableCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a variable (global or sprite-specific)"""
    project = crud.get_project(db, variable.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If sprite_id provided, verify it belongs to project
    if variable.sprite_id:
        sprite = crud.get_sprite(db, variable.sprite_id)
        if not sprite or sprite.project_id != variable.project_id:
            raise HTTPException(status_code=400, detail="Invalid sprite ID")
    
    return crud.create_variable(db=db, variable=variable)


@app.get("/api/v1/projects/{project_id}/variables", response_model=List[schemas.SpriteVariable])
def list_project_variables(
    project_id: int,
    sprite_id: Optional[int] = Query(None),
    global_only: bool = Query(False),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get variables for a project or sprite"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_project_variables(db, project_id, sprite_id, global_only)


@app.get("/api/v1/variables/{variable_id}", response_model=schemas.SpriteVariable)
def get_variable(
    variable_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific variable"""
    variable = crud.get_variable(db, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    
    project = crud.get_project(db, variable.project_id)
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return variable


@app.put("/api/v1/variables/{variable_id}", response_model=schemas.SpriteVariable)
def update_variable(
    variable_id: int,
    variable_update: schemas.SpriteVariableUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a variable"""
    variable = crud.get_variable(db, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    
    project = crud.get_project(db, variable.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_variable(db, variable_id, variable_update)


@app.delete("/api/v1/variables/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variable(
    variable_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a variable"""
    variable = crud.get_variable(db, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    
    project = crud.get_project(db, variable.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_variable(db, variable_id)
    return None


# ============================================================================
# SPRITE LIST ENDPOINTS
# ============================================================================

@app.post("/api/v1/lists", response_model=schemas.SpriteList, status_code=status.HTTP_201_CREATED)
def create_list(
    list_data: schemas.SpriteListCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a list (global or sprite-specific)"""
    project = crud.get_project(db, list_data.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # If sprite_id provided, verify it
    if list_data.sprite_id:
        sprite = crud.get_sprite(db, list_data.sprite_id)
        if not sprite or sprite.project_id != list_data.project_id:
            raise HTTPException(status_code=400, detail="Invalid sprite ID")
    
    return crud.create_list(db=db, list_data=list_data)


@app.get("/api/v1/projects/{project_id}/lists", response_model=List[schemas.SpriteList])
def list_project_lists(
    project_id: int,
    sprite_id: Optional[int] = Query(None),
    global_only: bool = Query(False),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get lists for a project or sprite"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.get_project_lists(db, project_id, sprite_id, global_only)


@app.put("/api/v1/lists/{list_id}", response_model=schemas.SpriteList)
def update_list(
    list_id: int,
    list_update: schemas.SpriteListUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a list"""
    list_obj = crud.get_list(db, list_id)
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    project = crud.get_project(db, list_obj.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.update_list(db, list_id, list_update)


@app.delete("/api/v1/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a list"""
    list_obj = crud.get_list(db, list_id)
    if not list_obj:
        raise HTTPException(status_code=404, detail="List not found")
    
    project = crud.get_project(db, list_obj.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    crud.delete_list(db, list_id)
    return None


# ============================================================================
# LIBRARY ENDPOINTS
# ============================================================================

@app.get("/api/v1/library/sprites", response_model=List[schemas.LibrarySprite])
def list_library_sprites(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get available sprites from library"""
    return crud.get_library_sprites(db, category, search, skip, limit)


@app.get("/api/v1/library/backdrops", response_model=List[schemas.LibraryBackdrop])
def list_library_backdrops(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get available backdrops from library"""
    return crud.get_library_backdrops(db, category, search, skip, limit)


@app.post("/api/v1/projects/{project_id}/library/sprite", response_model=schemas.Sprite)
def add_library_sprite_to_project(
    project_id: int,
    library_sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Add a library sprite to project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get library sprite
    library_sprite = db.query(models.LibrarySprite).filter(
        models.LibrarySprite.id == library_sprite_id
    ).first()
    
    if not library_sprite:
        raise HTTPException(status_code=404, detail="Library sprite not found")
    
    # Increment download count
    crud.increment_library_download_count(db, library_sprite_id, is_sprite=True)
    
    # Create sprite from library data
    sprite_data = library_sprite.sprite_data
    sprite_create = schemas.SpriteCreate(
        project_id=project_id,
        name=library_sprite.name,
        **{k: v for k, v in sprite_data.items() if k in ['x_position', 'y_position', 'direction', 'size']}
    )
    
    return crud.create_sprite(db, sprite_create)


@app.post("/api/v1/projects/{project_id}/library/backdrop", response_model=schemas.Backdrop)
def add_library_backdrop_to_project(
    project_id: int,    
    library_backdrop_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Add a library backdrop to project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get library backdrop
    library_backdrop = db.query(models.LibraryBackdrop).filter(
        models.LibraryBackdrop.id == library_backdrop_id
    ).first()
    
    if not library_backdrop:
        raise HTTPException(status_code=404, detail="Library backdrop not found")
    
    # Increment download count
    crud.increment_library_download_count(db, library_backdrop_id, is_sprite=False)
    
    # Create backdrop
    backdrop_create = schemas.BackdropCreate(
        project_id=project_id,
        name=library_backdrop.name,
        image_url=library_backdrop.image_url,
        width=library_backdrop.width,
        height=library_backdrop.height
    )
    
    return crud.create_backdrop(db, backdrop_create)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "blockly-backend"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)