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
import datetime
import models
import schemas
import crud
import auth
from database import engine, get_db
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta



# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Blockly Platform API",
    description="Backend API for Visual Programming Platform like PictoBlox",
    version="1.0.0",
    tags_metadata=[
        {
            "name": "Authentication",
            "description": "User registration, login, and profile management endpoints."
        },
        {
            "name": "Projects",
            "description": "Project management operations - create, read, update, delete, and duplicate projects."
        },
        {
            "name": "Sprites",
            "description": "Sprite management - create, update, delete sprites, manage positions, rotation, size, visibility, and layer ordering."
        },
        {
            "name": "Costumes",
            "description": "Costume management for sprites - create, upload, update, delete costumes and set active costume."
        },
        {
            "name": "Backdrops",
            "description": "Backdrop management for stage backgrounds - create, upload, update, and delete backdrops."
        },
        {
            "name": "Stage",
            "description": "Stage settings and configuration - dimensions, backdrop, audio, video, and performance settings."
        },
        {
            "name": "Variables",
            "description": "Variable management - create, read, update, delete global and sprite-specific variables."
        },
        {
            "name": "Lists",
            "description": "List management - create, read, update, delete global and sprite-specific lists."
        },
        {
            "name": "Code Execution",
            "description": "Execute Python or JavaScript code in a sandboxed environment with timeout and resource limits."
        },
        {
            "name": "Assets",
            "description": "General asset management - upload, list, and delete project assets (sprites, sounds, images, videos)."
        },
        {
            "name": "Library",
            "description": "Access pre-made sprites and backdrops from the library and add them to projects."
        },
        {
            "name": "Sharing",
            "description": "Project sharing and collaboration features - share projects with other users with permissions."
        },
        {
            "name": "Health",
            "description": "Health check and service status endpoints."
        },
    ]
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

@app.post("/api/v1/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    return crud.create_user(db=db, user=user)


@app.post("/api/v1/token", response_model=schemas.Token, tags=["Authentication"])
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


@app.get("/api/v1/users/me", response_model=schemas.User, tags=["Authentication"])
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """Get current user information"""
    return current_user


@app.put("/api/v1/users/me", response_model=schemas.User, tags=["Authentication"])
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

@app.post("/api/v1/projects", response_model=schemas.Project, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(
    project: schemas.ProjectCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    return crud.create_project(db=db, project=project, user_id=current_user.id)


@app.get("/api/v1/projects", response_model=List[schemas.Project], tags=["Projects"])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """List all projects for current user"""
    return crud.get_user_projects(db, user_id=current_user.id, skip=skip, limit=limit)


@app.get("/api/v1/projects/{project_id}", response_model=schemas.Project, tags=["Projects"])
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


@app.put("/api/v1/projects/{project_id}", response_model=schemas.Project, tags=["Projects"])
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


@app.delete("/api/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
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


@app.post("/api/v1/projects/{project_id}/duplicate", response_model=schemas.Project, tags=["Projects"])
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

@app.post("/api/v1/execute", response_model=schemas.ExecutionResult, tags=["Code Execution"])
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

@app.post("/api/v1/projects/{project_id}/assets", response_model=schemas.Asset, tags=["Assets"])
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


@app.get("/api/v1/projects/{project_id}/assets", response_model=List[schemas.Asset], tags=["Assets"])
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


@app.delete("/api/v1/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Assets"])
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

@app.get("/api/v1/projects/list/public", response_model=List[schemas.Project], tags=["Projects"])
def list_public_projects(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all public projects"""
    return crud.get_public_projects(db, skip=skip, limit=limit)


@app.post("/api/v1/projects/{project_id}/share", tags=["Sharing"])
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

@app.post("/api/v1/sprites", response_model=schemas.Sprite, status_code=status.HTTP_201_CREATED, tags=["Sprites"])
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


@app.get("/api/v1/projects/{project_id}/sprites", response_model=List[schemas.SpriteWithCostumes], tags=["Sprites"])
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


@app.get("/api/v1/sprites/{sprite_id}", response_model=schemas.SpriteComplete, tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}", response_model=schemas.Sprite, tags=["Sprites"])
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


@app.delete("/api/v1/sprites/{sprite_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Sprites"])
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


@app.post("/api/v1/sprites/{sprite_id}/duplicate", response_model=schemas.Sprite, tags=["Sprites"])
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


@app.put("/api/v1/projects/{project_id}/sprites/reorder", tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}/front", response_model=schemas.Sprite, tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}/back", response_model=schemas.Sprite, tags=["Sprites"])
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

@app.put("/api/v1/sprites/{sprite_id}/move", tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}/rotate", tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}/size", tags=["Sprites"])
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


@app.put("/api/v1/sprites/{sprite_id}/visibility", tags=["Sprites"])
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

@app.post("/api/v1/costumes", response_model=schemas.Costume, status_code=status.HTTP_201_CREATED, tags=["Costumes"])
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


@app.post("/api/v1/costumes/upload", response_model=schemas.Costume, tags=["Costumes"])
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


@app.get("/api/v1/sprites/{sprite_id}/costumes", response_model=List[schemas.Costume], tags=["Costumes"])
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


@app.put("/api/v1/costumes/{costume_id}", response_model=schemas.Costume, tags=["Costumes"])
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


@app.delete("/api/v1/costumes/{costume_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Costumes"])
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


@app.put("/api/v1/sprites/{sprite_id}/costume", response_model=schemas.Sprite, tags=["Costumes"])
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


@app.post("/api/v1/costumes/{costume_id}/duplicate", response_model=schemas.Costume, tags=["Costumes"])
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

@app.post("/api/v1/backdrops", response_model=schemas.Backdrop, status_code=status.HTTP_201_CREATED, tags=["Backdrops"])
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


@app.post("/api/v1/backdrops/upload", response_model=schemas.Backdrop, tags=["Backdrops"])
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


@app.get("/api/v1/projects/{project_id}/backdrops", response_model=List[schemas.Backdrop], tags=["Backdrops"])
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


@app.put("/api/v1/backdrops/{backdrop_id}", response_model=schemas.Backdrop, tags=["Backdrops"])
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


@app.delete("/api/v1/backdrops/{backdrop_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Backdrops"])
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

@app.get("/api/v1/projects/{project_id}/stage", response_model=schemas.StageSetting, tags=["Stage"])
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


@app.put("/api/v1/projects/{project_id}/stage", response_model=schemas.StageSetting, tags=["Stage"])
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


@app.put("/api/v1/projects/{project_id}/stage/backdrop", response_model=schemas.StageSetting, tags=["Stage"])
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


@app.get("/api/v1/projects/{project_id}/stage/complete", response_model=schemas.StageComplete, tags=["Stage"])
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

@app.post("/api/v1/variables", response_model=schemas.SpriteVariable, status_code=status.HTTP_201_CREATED, tags=["Variables"])
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


@app.get("/api/v1/projects/{project_id}/variables", response_model=List[schemas.SpriteVariable], tags=["Variables"])
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


@app.get("/api/v1/variables/{variable_id}", response_model=schemas.SpriteVariable, tags=["Variables"])
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


@app.put("/api/v1/variables/{variable_id}", response_model=schemas.SpriteVariable, tags=["Variables"])
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


@app.delete("/api/v1/variables/{variable_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Variables"])
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

@app.post("/api/v1/lists", response_model=schemas.SpriteList, status_code=status.HTTP_201_CREATED, tags=["Lists"])
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


@app.get("/api/v1/projects/{project_id}/lists", response_model=List[schemas.SpriteList], tags=["Lists"])
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


@app.put("/api/v1/lists/{list_id}", response_model=schemas.SpriteList, tags=["Lists"])
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


@app.delete("/api/v1/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Lists"])
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

@app.get("/api/v1/library/sprites", response_model=List[schemas.LibrarySprite], tags=["Library"])
def list_library_sprites(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get available sprites from library"""
    return crud.get_library_sprites(db, category, search, skip, limit)


@app.get("/api/v1/library/backdrops", response_model=List[schemas.LibraryBackdrop], tags=["Library"])
def list_library_backdrops(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get available backdrops from library"""
    return crud.get_library_backdrops(db, category, search, skip, limit)


@app.post("/api/v1/projects/{project_id}/library/sprite", response_model=schemas.Sprite, tags=["Library"])
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


@app.post("/api/v1/projects/{project_id}/library/backdrop", response_model=schemas.Backdrop, tags=["Library"])
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

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "blockly-backend"}


# ============================================================================
# SPRITE MOTION ENDPOINTS (Motion Blocks)
# ============================================================================

@app.put("/api/v1/sprites/{sprite_id}/motion/move", response_model=schemas.Sprite, tags=["Sprites"])
def move_sprite(
    sprite_id: int,
    steps: schemas.MotionMove,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Move the sprite 'steps' steps in its current direction."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # The actual calculation for new x, y will be in crud.move_sprite
    return crud.move_sprite(db, sprite_id=sprite_id, steps=steps.steps)


@app.put("/api/v1/sprites/{sprite_id}/motion/turn_right", response_model=schemas.Sprite, tags=["Sprites"])
def turn_right_sprite(
    sprite_id: int,
    degrees: schemas.MotionTurn,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Turn the sprite right (clockwise) by 'degrees'."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.turn_sprite(db, sprite_id=sprite_id, degrees=degrees.degrees, clockwise=True)


@app.put("/api/v1/sprites/{sprite_id}/motion/turn_left", response_model=schemas.Sprite, tags=["Sprites"])
def turn_left_sprite(
    sprite_id: int,
    degrees: schemas.MotionTurn,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Turn the sprite left (counter-clockwise) by 'degrees'."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return crud.turn_sprite(db, sprite_id=sprite_id, degrees=degrees.degrees, clockwise=False)


@app.put("/api/v1/sprites/{sprite_id}/motion/go_to", response_model=schemas.Sprite, tags=["Sprites"])
def go_to_position(
    sprite_id: int,
    # CHANGE: Use a single payload model
    goto_data: schemas.MotionGoToPayload, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Go to a specific x/y, random position, or target object (e.g., mouse-pointer)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.go_to_position(db, sprite_id=sprite_id, target=goto_data.target, x=goto_data.x, y=goto_data.y)


@app.put("/api/v1/sprites/{sprite_id}/motion/glide", response_model=schemas.Sprite, tags=["Sprites"])
def glide_to_position(
    sprite_id: int,
    glide_data: schemas.MotionGlide,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Glide to a specific position over a given duration. (The actual glide animation is client-side)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # For a real-time system, this would trigger an event/animation. 
    # Here, it just updates the position instantly after the 'glide' duration.
    return crud.glide_to_position(db, sprite_id=sprite_id, secs=glide_data.secs, target=glide_data.target, x=glide_data.x, y=glide_data.y)


@app.put("/api/v1/sprites/{sprite_id}/motion/set_direction", response_model=schemas.Sprite, tags=["Sprites"])
def point_in_direction(
    sprite_id: int,
    direction_data: schemas.MotionPointDirection,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set the sprite's direction (0-360 degrees)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_direction(db, sprite_id=sprite_id, direction=direction_data.direction)

@app.put("/api/v1/sprites/{sprite_id}/motion/point_towards", response_model=schemas.Sprite, tags=["Sprites"])
def point_towards_target(
    sprite_id: int,
    # CHANGE THIS LINE: Use the comprehensive payload model
    point_data: schemas.MotionPointTowardsPayload, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Point the sprite towards a target (e.g., mouse-pointer or another sprite ID)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Pass the fields from the payload object to the CRUD function
    return crud.point_sprite_towards(
        db, 
        sprite_id=sprite_id, 
        target=point_data.target, # target field from the payload
        x=point_data.x, 
        y=point_data.y
    )

# @app.put("/api/v1/sprites/{sprite_id}/motion/point_towards", response_model=schemas.Sprite, tags=["Sprites"])
# def point_towards_target(
#     sprite_id: int,
#     point_data: schemas.MotionPointTowardsPayload,
#     target: schemas.MotionPointTowardsTarget,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Point the sprite towards a target (e.g., mouse-pointer or another sprite ID)."""
#     sprite = crud.get_sprite(db, sprite_id)
#     if not sprite:
#         raise HTTPException(status_code=404, detail="Sprite not found")
#     project = crud.get_project(db, sprite.project_id)
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     # The actual calculation (atan2) for the new direction will be in crud.point_towards
#     return crud.point_sprite_towards(db, sprite_id=sprite_id, target=point_data.target, x=point_data.x, y=point_data.y)


@app.put("/api/v1/sprites/{sprite_id}/motion/change_x", response_model=schemas.Sprite, tags=["Sprites"])
def change_x_by(
    sprite_id: int,
    change_x: schemas.MotionChangePosition,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change the sprite's x position by an amount."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.change_sprite_x(db, sprite_id=sprite_id, change=change_x.change)


@app.put("/api/v1/sprites/{sprite_id}/motion/set_x", response_model=schemas.Sprite, tags=["Sprites"])
def set_x_to(
    sprite_id: int,
    set_x: schemas.MotionSetPosition,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set the sprite's x position to a specific value."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_x(db, sprite_id=sprite_id, value=set_x.value)


@app.put("/api/v1/sprites/{sprite_id}/motion/change_y", response_model=schemas.Sprite, tags=["Sprites"])
def change_y_by(
    sprite_id: int,
    change_y: schemas.MotionChangePosition,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change the sprite's y position by an amount."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.change_sprite_y(db, sprite_id=sprite_id, change=change_y.change)


@app.put("/api/v1/sprites/{sprite_id}/motion/set_y", response_model=schemas.Sprite, tags=["Sprites"])
def set_y_to(
    sprite_id: int,
    set_y: schemas.MotionSetPosition,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set the sprite's y position to a specific value."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_y(db, sprite_id=sprite_id, value=set_y.value)


@app.put("/api/v1/sprites/{sprite_id}/motion/if_on_edge_bounce", response_model=schemas.Sprite, tags=["Sprites"])
def if_on_edge_bounce(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """If the sprite is touching the edge of the stage, reverse its direction."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # The actual check and direction update is in crud.if_on_edge_bounce
    return crud.if_on_edge_bounce(db, sprite_id=sprite_id)


@app.put("/api/v1/sprites/{sprite_id}/motion/set_rotation_style", response_model=schemas.Sprite, tags=["Sprites"])
def set_rotation_style(
    sprite_id: int,
    style: schemas.MotionSetRotationStyle,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set the sprite's rotation style (all around, left-right, or don't rotate)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_rotation_style(db, sprite_id=sprite_id, rotation_style=style.rotation_style)


@app.get("/api/v1/sprites/{sprite_id}/motion/get_x", response_model=schemas.MotionPositionValue, tags=["Sprites"])
def get_x_position(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reporter block: Get the sprite's current X position."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    # Allow read access if project is public
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {"value": sprite.x_position}

@app.get("/api/v1/sprites/{sprite_id}/motion/get_y", response_model=schemas.MotionPositionValue, tags=["Sprites"])
def get_y_position(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reporter block: Get the sprite's current Y position."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {"value": sprite.y_position}

@app.get("/api/v1/sprites/{sprite_id}/motion/get_direction", response_model=schemas.MotionPositionValue, tags=["Sprites"])
def get_direction(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reporter block: Get the sprite's current direction."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite:
        raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {"value": sprite.direction}

# ============================================================================
#LOOKS BLOCK ENDPOINT
# ============================================================================


@app.put("/api/v1/sprites/{sprite_id}/looks/say", response_model=schemas.Sprite, tags=["Looks"])
def say_message(
    sprite_id: int,
    say_data: schemas.LookSayThink,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Say a message for a duration or indefinitely."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_message(db, sprite_id=sprite_id, message=say_data.message, action=schemas.LookMessageAction.SAY, secs=say_data.secs)

@app.put("/api/v1/sprites/{sprite_id}/looks/think", response_model=schemas.Sprite, tags=["Looks"])
def think_message(
    sprite_id: int,
    think_data: schemas.LookSayThink,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Think a message for a duration or indefinitely."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_message(db, sprite_id=sprite_id, message=think_data.message, action=schemas.LookMessageAction.THINK, secs=think_data.secs)

@app.put("/api/v1/sprites/{sprite_id}/looks/switch_costume", response_model=schemas.Sprite, tags=["Looks"])
def switch_costume(
    sprite_id: int,
    # CHANGE THIS LINE: Replace MotionPointTowardsTarget with the new schema
    costume_data: schemas.LookSwitchCostumePayload, 
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Switch the sprite's current costume to a named costume."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    # The rest of the logic is now correct:
    return crud.switch_sprite_costume(db, sprite_id=sprite_id, costume_name=costume_data.target)

# @app.put("/api/v1/sprites/{sprite_id}/looks/switch_costume", response_model=schemas.Sprite, tags=["Looks"])
# def switch_costume(
#     sprite_id: int,
#     costume_data: schemas.MotionPointTowardsTarget, # Reusing a simple string payload model if available
#     current_user: models.User = Depends(auth.get_current_user),
    
#     db: Session = Depends(get_db)
# ):
#     """Switch the sprite's current costume to a named costume."""
#     sprite = crud.get_sprite(db, sprite_id)
#     if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
#     project = crud.get_project(db, sprite.project_id)
#     if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

#     return crud.switch_sprite_costume(db, sprite_id=sprite_id, costume_name=costume_data.target)

@app.put("/api/v1/sprites/{sprite_id}/looks/next_costume", response_model=schemas.Sprite, tags=["Looks"])
def next_costume(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Switch to the next costume in the list."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.switch_sprite_costume(db, sprite_id=sprite_id, costume_name=None) 


@app.put("/api/v1/sprites/{sprite_id}/looks/change_size", response_model=schemas.Sprite, tags=["Looks"])
def change_size(
    sprite_id: int,
    size_data: schemas.LookChangeSize,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change the sprite's size by an amount (percentage)."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.change_sprite_size(db, sprite_id=sprite_id, change=size_data.change)


@app.put("/api/v1/sprites/{sprite_id}/looks/set_size", response_model=schemas.Sprite, tags=["Looks"])
def set_size(
    sprite_id: int,
    size_data: schemas.LookSetSize,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set the sprite's size to a percentage."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_size(db, sprite_id=sprite_id, percent=size_data.percent)


# --- Backdrop Blocks ---

@app.put("/api/v1/projects/{project_id}/switch-backdrop/{backdrop_id}", response_model=schemas.StageSetting, tags=["Backdrops"])
def switch_backdrop_by_id(
    project_id: int,
    backdrop_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Block: switch backdrop to [backdrop_id]"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    updated_stage = crud.switch_project_backdrop(db, project_id, target_backdrop_id=backdrop_id)
    if not updated_stage:
        raise HTTPException(status_code=404, detail="Backdrop not found for this project")
        
    return updated_stage

@app.put("/api/v1/projects/{project_id}/next-backdrop", response_model=schemas.StageSetting, tags=["Backdrops"])
def next_backdrop(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Block: next backdrop"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    updated_stage = crud.next_project_backdrop(db, project_id)
    if not updated_stage:
        raise HTTPException(status_code=400, detail="Failed to switch to next backdrop (no backdrops found)")
        
    return updated_stage

@app.put("/api/v1/sprites/{sprite_id}/looks/change_effect", response_model=schemas.Sprite, tags=["Looks"])
def change_effect(
    sprite_id: int,
    effect_data: schemas.LookChangeEffect,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Change a specific graphic effect by an amount."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    # The CRUD function handles both change and set, needing context.
    # Set db.info flag to signal 'change' operation to crud function logic
    db.info['change_effect'] = True 
    result = crud.set_graphic_effect(db, sprite_id=sprite_id, effect=effect_data.effect, value=effect_data.change)
    db.info['change_effect'] = False # Clear flag
    return result


@app.put("/api/v1/sprites/{sprite_id}/looks/set_effect", response_model=schemas.Sprite, tags=["Looks"])
def set_effect(
    sprite_id: int,
    effect_data: schemas.LookSetEffect,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Set a specific graphic effect to a specific value."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_graphic_effect(db, sprite_id=sprite_id, effect=effect_data.effect, value=effect_data.value)


@app.put("/api/v1/sprites/{sprite_id}/looks/clear_effects", response_model=schemas.Sprite, tags=["Looks"])
def clear_effects(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all graphic effects."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.clear_graphic_effects(db, sprite_id=sprite_id)


@app.put("/api/v1/sprites/{sprite_id}/looks/show", response_model=schemas.Sprite, tags=["Looks"])
def show_sprite(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Show the sprite."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_visibility(db, sprite_id=sprite_id, is_visible=True)


@app.put("/api/v1/sprites/{sprite_id}/looks/hide", response_model=schemas.Sprite, tags=["Looks"])
def hide_sprite(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Hide the sprite."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_visibility(db, sprite_id=sprite_id, is_visible=False)


@app.put("/api/v1/sprites/{sprite_id}/looks/go_to_layer", response_model=schemas.Sprite, tags=["Looks"])
def go_to_layer(
    sprite_id: int,
    layer_data: schemas.LookGoToLayer,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Go to the front or back layer."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.set_sprite_layer(db, sprite_id=sprite_id, layer=layer_data.layer)


@app.put("/api/v1/sprites/{sprite_id}/looks/change_layer", response_model=schemas.Sprite, tags=["Looks"])
def change_layer(
    sprite_id: int,
    layer_data: schemas.LookChangeLayer,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Go forward or backward by a number of layers."""
    # ... authorization checks ...
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized")

    return crud.change_sprite_layer(db, sprite_id=sprite_id, forward_layers=layer_data.forward_layers)


# --- Looks Reporter Endpoints (GET) ---

@app.get("/api/v1/sprites/{sprite_id}/looks/get_costume", response_model=schemas.LookReporterValue, tags=["Looks"])
def get_costume_number(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reporter block: Get the sprite's current costume number."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id and not project.is_public: raise HTTPException(status_code=403, detail="Not authorized")
    
    # Assuming sprite.current_costume_id holds the number or can be easily looked up
    return {"value": sprite.current_costume_id or 1.0}


@app.get("/api/v1/sprites/{sprite_id}/looks/get_size", response_model=schemas.LookReporterValue, tags=["Looks"])
def get_size(
    sprite_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Reporter block: Get the sprite's current size (percentage)."""
    sprite = crud.get_sprite(db, sprite_id)
    if not sprite: raise HTTPException(status_code=404, detail="Sprite not found")
    project = crud.get_project(db, sprite.project_id)
    if project.user_id != current_user.id and not project.is_public: raise HTTPException(status_code=403, detail="Not authorized")

    return {"value": sprite.size}

# ============================================================================
# EVENT MESSAGING ENDPOINTS
# ============================================================================

@app.post("/api/v1/projects/{project_id}/messages", response_model=schemas.Message, status_code=status.HTTP_201_CREATED, tags=["Events"])
def create_project_message(
    project_id: int,
    message: schemas.MessageCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new named message (e.g., 'message1') for use in broadcast blocks"""
    if message.project_id != project_id:
        raise HTTPException(status_code=400, detail="Project ID mismatch")

    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return crud.create_message(db, message=message)

@app.get("/api/v1/projects/{project_id}/messages", response_model=List[schemas.Message], tags=["Events"])
def list_project_messages(
    project_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all predefined messages for a project"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check access rights (allowing public access if project is public)
    if project.user_id != current_user.id and not project.is_public:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return crud.get_project_messages(db, project_id=project_id)


# ============================================================================
# EVENT EXECUTION BLOCKS
# ============================================================================

@app.post("/api/v1/projects/{project_id}/broadcast", tags=["Events"])
def broadcast_message(
    project_id: int,
    request: schemas.BroadcastRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Block: broadcast [message1] OR broadcast [message1] and wait"""
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Authorization check: only the owner/editor should initiate backend code events
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to run/modify this project")
    
    # 1. Log the broadcast event in the database
    log = crud.log_broadcast(db, project_id, request.message_name, request.wait, current_user.id)

    # 2. Key Action: Signal the client (frontend) interpreter
    # In a real-time system (using WebSockets/SSE), this API would trigger a 
    # message to all connected clients viewing this project.
    
    # Placeholder response to signal success
    action = "broadcast and wait" if request.wait else "broadcast"
    return {
        "message": f"'{request.message_name}' {action} initiated.",
        "log_id": log.id,
        "waits_for_completion": request.wait
    }


# ============================================================================
# EVENT LISTENERS (Simulated Triggers)
# ============================================================================

# NOTE: The "when [flag] clicked", "when [key] pressed", "when stage clicked", 
# "when backdrop switches", and "when I receive [message]" blocks are typically 
# **listeners** handled by the client-side JavaScript interpreter. 

# However, we can create API endpoints to signal these events, especially for 
# remote control or testing purposes, which the client interpreter listens to.

@app.post("/api/v1/projects/{project_id}/trigger-event/{event_name}", tags=["Events"])
def trigger_system_event(
    project_id: int,
    event_name: str, # e.g., "green_flag", "key_space", "stage_click", "loudness_high"
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulates a system event trigger (like Green Flag Clicked) 
    that the client-side interpreter will pick up and execute.
    """
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # In a real application, this would trigger a WebSocket message to the client.
    return {"message": f"Event '{event_name}' signaled for project {project_id}"}


# ============================================================================
# SENSING EVENT ENDPOINTS (Loudness, Timer, etc.)
# ============================================================================

@app.post("/api/v1/sensor-data", status_code=status.HTTP_202_ACCEPTED, tags=["Sensing", "Events"])
def report_sensor_data(
    report: schemas.SensorDataReport,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handles real-time sensor data reports from the client (e.g., loudness, timer).
    The client interpreter uses this data to evaluate 'when loudness > 10' blocks.
    """
    project = crud.get_project(db, report.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Check if the user is authorized to run this project (or is the owner)
    if project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to run project scripts")
    
    # NOTE: In a production environment, this data would likely be logged 
    # to a fast NoSQL store or handled via WebSockets, not SQLAlchemy.
    
    # Placeholder: The backend acknowledges the report.
    # The client (interpreter) is responsible for running the 'when loudness > X' script 
    # if the condition (report.value > X) is met.
    
    return {
        "message": f"Sensor data '{report.sensor_name}' reported with value {report.value}",
        "project_id": report.project_id
    }

# # ============================================================================
# # EVENT BINDING ENDPOINTS
# # ============================================================================

# @app.post("/api/v1/events/bindings", response_model=schemas.EventBinding, status_code=status.HTTP_201_CREATED)
# def create_event_binding(
#     binding: schemas.EventBindingCreate,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Create a new event binding (link event to script)
   
#     Example: When green flag clicked, run script
#     """
#     # Verify project ownership
#     project = db.query(models.Project).filter(models.Project.id == binding.project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     # Verify sprite if provided
#     if binding.sprite_id:
#         sprite = db.query(models.Sprite).filter(models.Sprite.id == binding.sprite_id).first()
#         if not sprite or sprite.project_id != binding.project_id:
#             raise HTTPException(status_code=400, detail="Invalid sprite ID")
   
#     # Create event binding
#     db_binding = models.EventBinding(**binding.dict())
#     db.add(db_binding)
#     db.commit()
#     db.refresh(db_binding)
   
#     return db_binding


# @app.get("/api/v1/projects/{project_id}/events/bindings", response_model=List[schemas.EventBinding])
# def list_project_event_bindings(
#     project_id: int,
#     sprite_id: Optional[int] = Query(None),
#     event_type: Optional[str] = Query(None),
#     active_only: bool = Query(True),
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all event bindings for a project"""
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id and not project.is_public:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     query = db.query(models.EventBinding).filter(models.EventBinding.project_id == project_id)
   
#     if sprite_id is not None:
#         query = query.filter(models.EventBinding.sprite_id == sprite_id)
   
#     if event_type:
#         query = query.filter(models.EventBinding.event_type == event_type)
   
#     if active_only:
#         query = query.filter(models.EventBinding.is_active == True)
   
#     return query.order_by(models.EventBinding.execution_order).all()


# @app.get("/api/v1/events/bindings/{binding_id}", response_model=schemas.EventBinding)
# def get_event_binding(
#     binding_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get a specific event binding"""
#     binding = db.query(models.EventBinding).filter(models.EventBinding.id == binding_id).first()
#     if not binding:
#         raise HTTPException(status_code=404, detail="Event binding not found")
   
#     project = db.query(models.Project).filter(models.Project.id == binding.project_id).first()
#     if project.user_id != current_user.id and not project.is_public:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     return binding


# @app.put("/api/v1/events/bindings/{binding_id}", response_model=schemas.EventBinding)
# def update_event_binding(
#     binding_id: int,
#     binding_update: schemas.EventBindingUpdate,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Update an event binding"""
#     binding = db.query(models.EventBinding).filter(models.EventBinding.id == binding_id).first()
#     if not binding:
#         raise HTTPException(status_code=404, detail="Event binding not found")
   
#     project = db.query(models.Project).filter(models.Project.id == binding.project_id).first()
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     # Update fields
#     update_data = binding_update.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(binding, field, value)
   
#     db.commit()
#     db.refresh(binding)
#     return binding


# @app.delete("/api/v1/events/bindings/{binding_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_event_binding(
#     binding_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Delete an event binding"""
#     binding = db.query(models.EventBinding).filter(models.EventBinding.id == binding_id).first()
#     if not binding:
#         raise HTTPException(status_code=404, detail="Event binding not found")
   
#     project = db.query(models.Project).filter(models.Project.id == binding.project_id).first()
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     db.delete(binding)
#     db.commit()
#     return None


# # ============================================================================
# # BROADCAST MESSAGE ENDPOINTS
# # ============================================================================

# @app.post("/api/v1/broadcasts", response_model=schemas.BroadcastMessage, status_code=status.HTTP_201_CREATED)
# def create_broadcast_message(
#     message: schemas.BroadcastMessageCreate,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Create a new broadcast message definition"""
#     project = db.query(models.Project).filter(models.Project.id == message.project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     # Check if message name already exists
#     existing = db.query(models.BroadcastMessage).filter(
#         models.BroadcastMessage.project_id == message.project_id,
#         models.BroadcastMessage.name == message.name
#     ).first()
   
#     if existing:
#         raise HTTPException(status_code=400, detail="Broadcast message with this name already exists")
   
#     db_message = models.BroadcastMessage(**message.dict())
#     db.add(db_message)
#     db.commit()
#     db.refresh(db_message)
   
#     return db_message


# @app.get("/api/v1/projects/{project_id}/broadcasts", response_model=List[schemas.BroadcastMessage])
# def list_broadcast_messages(
#     project_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get all broadcast messages for a project"""
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id and not project.is_public:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     return db.query(models.BroadcastMessage)\
#         .filter(models.BroadcastMessage.project_id == project_id)\
#         .all()


# @app.put("/api/v1/broadcasts/{message_id}", response_model=schemas.BroadcastMessage)
# def update_broadcast_message(
#     message_id: int,
#     message_update: schemas.BroadcastMessageUpdate,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Update a broadcast message"""
#     message = db.query(models.BroadcastMessage).filter(models.BroadcastMessage.id == message_id).first()
#     if not message:
#         raise HTTPException(status_code=404, detail="Broadcast message not found")
   
#     project = db.query(models.Project).filter(models.Project.id == message.project_id).first()
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     update_data = message_update.dict(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(message, field, value)
   
#     db.commit()
#     db.refresh(message)
#     return message


# @app.delete("/api/v1/broadcasts/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_broadcast_message(
#     message_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Delete a broadcast message"""
#     message = db.query(models.BroadcastMessage).filter(models.BroadcastMessage.id == message_id).first()
#     if not message:
#         raise HTTPException(status_code=404, detail="Broadcast message not found")
   
#     project = db.query(models.Project).filter(models.Project.id == message.project_id).first()
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     db.delete(message)
#     db.commit()
#     return None


# # ============================================================================
# # EVENT TRIGGERING ENDPOINTS (Runtime)
# # ============================================================================

# @app.post("/api/v1/projects/{project_id}/events/trigger")
# async def trigger_event(
#     project_id: int,
#     trigger_request: schemas.TriggerEventRequest,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Trigger an event and execute all matching handlers
   
#     Examples:
#     - Trigger "when clicked": {"event_type": "when_clicked", "event_data": {}}
#     - Trigger key press: {"event_type": "when_key_pressed", "event_data": {"key": "space"}}
#     - Trigger broadcast: {"event_type": "when_broadcast_received", "event_data": {"message": "start"}}
#     """
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     # Find matching event bindings
#     bindings = db.query(models.EventBinding).filter(
#         models.EventBinding.project_id == project_id,
#         models.EventBinding.event_type == trigger_request.event_type.value,
#         models.EventBinding.is_active == True
#     ).order_by(models.EventBinding.execution_order).all()
   
#     # Filter bindings based on event data
#     matching_bindings = []
#     for binding in bindings:
#         if _matches_event_data(binding, trigger_request.event_data):
#             matching_bindings.append(binding)
   
#     # Execute handlers
#     results = []
#     for binding in matching_bindings:
#         result = await _execute_event_handler(binding, trigger_request.event_data, db)
#         results.append(result)
   
#     # Log event
#     event_log = models.EventLog(
#         project_id=project_id,
#         user_id=current_user.id,
#         event_type=trigger_request.event_type.value,
#         event_data=trigger_request.event_data,
#         handlers_executed=len(results),
#         execution_time=sum(r.get('execution_time', 0) for r in results)
#     )
#     db.add(event_log)
#     db.commit()
   
#     return {
#         "event_type": trigger_request.event_type,
#         "handlers_executed": len(results),
#         "results": results
#     }


# @app.post("/api/v1/projects/{project_id}/broadcast")
# async def broadcast_message(
#     project_id: int,
#     broadcast_request: schemas.BroadcastRequest,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """
#     Broadcast a message to all listening sprites
   
#     Example: {"message_name": "start game", "wait": false}
#     """
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     if project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized")
   
#     # Find all "when I receive [message]" handlers
#     bindings = db.query(models.EventBinding).filter(
#         models.EventBinding.project_id == project_id,
#         models.EventBinding.event_type == "when_broadcast_received",
#         models.EventBinding.is_active == True
#     ).all()
   
#     # Filter by message name
#     matching_bindings = [
#         b for b in bindings
#         if b.handler_data.get('message_name') == broadcast_request.message_name
#     ]
   
#     # Execute handlers
#     results = []
#     for binding in matching_bindings:
#         result = await _execute_event_handler(binding, broadcast_request.data, db)
#         results.append(result)
       
#         if not broadcast_request.wait:
#             # Don't wait for completion
#             continue
   
#     return {
#         "message": broadcast_request.message_name,
#         "handlers_executed": len(results),
#         "results": results if broadcast_request.wait else None
#     }


# # ============================================================================
# # KEYBOARD STATE ENDPOINTS
# # ============================================================================

# @app.post("/api/v1/projects/{project_id}/keyboard/press")
# def handle_key_press(
#     project_id: int,
#     key_event: schemas.KeyPressEvent,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Handle key press event"""
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     # Get or create keyboard state
#     kb_state = db.query(models.KeyboardState).filter(
#         models.KeyboardState.project_id == project_id
#     ).first()
   
#     if not kb_state:
#         kb_state = models.KeyboardState(project_id=project_id, pressed_keys=[])
#         db.add(kb_state)
   
#     # Update state
#     pressed_keys = kb_state.pressed_keys or []
#     if key_event.key.value not in pressed_keys:
#         pressed_keys.append(key_event.key.value)
   
#     kb_state.pressed_keys = pressed_keys
#     kb_state.last_key = key_event.key.value
#     kb_state.last_press_time = key_event.timestamp
   
#     db.commit()
   
#     # Trigger "when key pressed" events
#     trigger_data = schemas.TriggerEventRequest(
#         event_type=schemas.EventType.WHEN_KEY_PRESSED,
#         event_data={"key": key_event.key.value}
#     )
   
#     return {"status": "key_pressed", "key": key_event.key.value}


# @app.post("/api/v1/projects/{project_id}/keyboard/release")
# def handle_key_release(
#     project_id: int,
#     key_event: schemas.KeyReleaseEvent,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Handle key release event"""
#     kb_state = db.query(models.KeyboardState).filter(
#         models.KeyboardState.project_id == project_id
#     ).first()
   
#     if kb_state:
#         pressed_keys = kb_state.pressed_keys or []
#         if key_event.key.value in pressed_keys:
#             pressed_keys.remove(key_event.key.value)
#         kb_state.pressed_keys = pressed_keys
#         db.commit()
   
#     return {"status": "key_released", "key": key_event.key.value}


# @app.get("/api/v1/projects/{project_id}/keyboard/state", response_model=schemas.KeyboardState)
# def get_keyboard_state(
#     project_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current keyboard state"""
#     kb_state = db.query(models.KeyboardState).filter(
#         models.KeyboardState.project_id == project_id
#     ).first()
   
#     if not kb_state:
#         return schemas.KeyboardState(pressed_keys=[], last_key=None)
   
#     return schemas.KeyboardState(
#         pressed_keys=[schemas.KeyType(k) for k in (kb_state.pressed_keys or [])],
#         last_key=schemas.KeyType(kb_state.last_key) if kb_state.last_key else None,
#         last_press_time=kb_state.last_press_time
#     )


# # ============================================================================
# # TIMER ENDPOINTS
# # ============================================================================

# @app.get("/api/v1/projects/{project_id}/timer", response_model=schemas.TimerState)
# def get_timer_state(
#     project_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get current timer value"""
#     timer = db.query(models.TimerState).filter(
#         models.TimerState.project_id == project_id
#     ).first()
   
#     if not timer:
#         # Create default timer
#         timer = models.TimerState(project_id=project_id, current_value=0.0, is_running=True)
#         db.add(timer)
#         db.commit()
#         db.refresh(timer)
   
#     # Calculate current value if running
#     if timer.is_running:
#         elapsed = (datetime.utcnow() - timer.started_at).total_seconds()
#         timer.current_value = elapsed
   
#     return schemas.TimerState(
#         project_id=project_id,
#         current_value=timer.current_value,
#         is_running=timer.is_running,
#         started_at=timer.started_at
#     )


# @app.post("/api/v1/projects/{project_id}/timer/reset")
# def reset_timer(
#     project_id: int,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Reset timer to 0"""
#     timer = db.query(models.TimerState).filter(
#         models.TimerState.project_id == project_id
#     ).first()
   
#     if not timer:
#         timer = models.TimerState(project_id=project_id)
#         db.add(timer)
   
#     timer.current_value = 0.0
#     timer.started_at = datetime.utcnow()
#     timer.is_running = True
   
#     db.commit()
   
#     return {"message": "Timer reset", "value": 0.0}


# # ============================================================================
# # SENSOR READING ENDPOINTS
# # ============================================================================

# @app.post("/api/v1/projects/{project_id}/sensors/reading")
# def record_sensor_reading(
#     project_id: int,
#     reading: schemas.SensorReading,
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Record a sensor reading (loudness, video motion, etc.)"""
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
   
#     db_reading = models.SensorReading(
#         project_id=project_id,
#         sensor_type=reading.sensor_type.value,
#         value=reading.value
#     )
#     db.add(db_reading)
#     db.commit()
   
#     # Check for "when greater than" triggers
#     _check_sensor_triggers(project_id, reading.sensor_type.value, reading.value, db)
   
#     return {"status": "recorded", "sensor": reading.sensor_type, "value": reading.value}


# @app.get("/api/v1/projects/{project_id}/sensors/latest")
# def get_latest_sensor_readings(
#     project_id: int,
#     sensor_type: Optional[str] = Query(None),
#     current_user: models.User = Depends(auth.get_current_user),
#     db: Session = Depends(get_db)
# ):
#     """Get latest sensor readings"""
#     query = db.query(models.SensorReading).filter(
#         models.SensorReading.project_id == project_id
#     )
   
#     if sensor_type:
#         query = query.filter(models.SensorReading.sensor_type == sensor_type)
   
#     readings = query.order_by(models.SensorReading.recorded_at.desc()).limit(10).all()
   
#     return [
#         {
#             "sensor_type": r.sensor_type,
#             "value": r.value,
#             "recorded_at": r.recorded_at
#         }
#         for r in readings
#     ]


# # ============================================================================
# # HELPER FUNCTIONS
# # ============================================================================

# def _matches_event_data(binding: models.EventBinding, event_data: Dict[str, Any]) -> bool:
#     """Check if event data matches handler requirements"""
#     handler_data = binding.handler_data or {}
   
#     # For key press events
#     if binding.event_type == "when_key_pressed":
#         required_key = handler_data.get('key')
#         actual_key = event_data.get('key')
#         return required_key == actual_key or required_key == 'any'
   
#     # For backdrop switch events
#     if binding.event_type == "when_backdrop_switches":
#         required_backdrop = handler_data.get('backdrop_id')
#         actual_backdrop = event_data.get('backdrop_id')
#         return required_backdrop == actual_backdrop or required_backdrop is None
   
#     # For broadcast events
#     if binding.event_type == "when_broadcast_received":
#         required_message = handler_data.get('message_name')
#         actual_message = event_data.get('message') or event_data.get('message_name')
#         return required_message == actual_message
   
#     # Default: match
#     return True


# async def _execute_event_handler(
#     binding: models.EventBinding,
#     event_data: Dict[str, Any],
#     db: Session
# ) -> Dict[str, Any]:
#     """Execute an event handler's script"""
#     import time
#     start_time = time.time()
   
#     try:
#         # Here you would execute the script_blocks
#         # For now, return mock execution
       
#         # TODO: Integrate with your code execution engine
#         script_blocks = binding.script_blocks or []
       
#         execution_time = time.time() - start_time
       
#         return {
#             "binding_id": binding.id,
#             "success": True,
#             "blocks_executed": len(script_blocks),
#             "execution_time": execution_time
#         }
       
#     except Exception as e:
#         execution_time = time.time() - start_time
#         return {
#             "binding_id": binding.id,
#             "success": False,
#             "error": str(e),
#             "execution_time": execution_time
#         }


# def _check_sensor_triggers(project_id: int, sensor_type: str, value: float, db: Session):
#     """Check if sensor value triggers any 'when greater than' events"""
#     bindings = db.query(models.EventBinding).filter(
#         models.EventBinding.project_id == project_id,
#         models.EventBinding.event_type == "when_greater_than",
#         models.EventBinding.is_active == True
#     ).all()
   
#     for binding in bindings:
#         handler_data = binding.handler_data or {}
#         if handler_data.get('sensor_type') == sensor_type:
#             threshold = handler_data.get('threshold_value', 0)
#             if value > threshold:
#                 # Trigger event
#                 # TODO: Execute handler asynchronously
#                 pass 


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)



