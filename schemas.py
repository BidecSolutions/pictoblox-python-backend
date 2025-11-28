"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import UserRole, ProjectStatus, AssetType


# ============================================================================
# USER SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):                            
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class User(UserBase):
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ============================================================================
# PROJECT SCHEMAS
# ============================================================================

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_public: bool = False
    is_template: bool = False


class ProjectCreate(ProjectBase):
    workspace_xml: Optional[str] = None
    workspace_json: Optional[Dict[str, Any]] = None
    code_language: str = "python"


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    workspace_xml: Optional[str] = None
    workspace_json: Optional[Dict[str, Any]] = None
    generated_code: Optional[str] = None
    code_language: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_public: Optional[bool] = None
    status: Optional[ProjectStatus] = None


class Project(ProjectBase):
    id: int
    user_id: int
    workspace_xml: Optional[str] = None
    workspace_json: Optional[Dict[str, Any]] = None
    generated_code: Optional[str] = None
    code_language: str
    thumbnail_url: Optional[str] = None
    status: ProjectStatus
    version: int
    parent_project_id: Optional[int] = None
    view_count: int
    like_count: int
    fork_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectWithOwner(Project):
    owner: User


class ProjectListItem(BaseModel):
    """Lightweight project info for listing"""
    id: int
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: ProjectStatus
    is_public: bool
    view_count: int
    like_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# ASSET SCHEMAS
# ============================================================================

class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    asset_type: AssetType


class AssetCreate(AssetBase):
    file_url: Optional[str] = None
    data_base64: Optional[str] = None
    mime_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None


class Asset(AssetBase):
    id: int
    project_id: int
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# CODE EXECUTION SCHEMAS
# ============================================================================

class CodeExecution(BaseModel):
    code: str
    language: str = "python"
    project_id: Optional[int] = None
    timeout: int = Field(default=10, ge=1, le=60)  # 1-60 seconds
    
    @validator('language')
    def validate_language(cls, v):
        allowed = ['python', 'javascript']
        if v not in allowed:
            raise ValueError(f'Language must be one of {allowed}')
        return v


class ExecutionResult(BaseModel):
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    exit_code: int = 0
    success: bool = True


class ExecutionLog(BaseModel):
    id: int
    user_id: int
    project_id: Optional[int] = None
    code: str
    language: str
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float
    exit_code: int
    executed_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SHARING SCHEMAS
# ============================================================================

class ProjectShare(BaseModel):
    user_id: int
    can_edit: bool = False
    can_view: bool = True
    can_execute: bool = True


class ProjectShareInfo(BaseModel):
    id: int
    project_id: int
    shared_with_user_id: int
    can_edit: bool
    can_view: bool
    can_execute: bool
    shared_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# EXTENSION SCHEMAS
# ============================================================================

class ExtensionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str
    description: Optional[str] = None
    category: Optional[str] = None


class ExtensionCreate(ExtensionBase):
    block_definitions: Dict[str, Any]
    generator_code: str
    version: str = "1.0.0"
    author: Optional[str] = None
    icon_url: Optional[str] = None


class Extension(ExtensionBase):
    id: int
    block_definitions: Dict[str, Any]
    generator_code: str
    version: str
    author: Optional[str] = None
    icon_url: Optional[str] = None
    is_active: bool
    is_official: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# HARDWARE DEVICE SCHEMAS
# ============================================================================

class HardwareDeviceBase(BaseModel):
    device_name: str
    device_type: str
    serial_number: Optional[str] = None


class HardwareDeviceCreate(HardwareDeviceBase):
    port: Optional[str] = None
    baud_rate: Optional[int] = 9600
    capabilities: Optional[Dict[str, Any]] = None


class HardwareDevice(HardwareDeviceBase):
    id: int
    user_id: int
    port: Optional[str] = None
    baud_rate: Optional[int] = None
    is_connected: bool
    firmware_version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    last_connected_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STATISTICS SCHEMAS
# ============================================================================

class UserStats(BaseModel):
    total_projects: int
    public_projects: int
    total_executions: int
    total_views: int


class ProjectStats(BaseModel):
    total_projects: int
    public_projects: int
    draft_projects: int
    archived_projects: int



class SpriteBase(BaseModel):
    """Base sprite schema"""
    name: str = Field(..., min_length=1, max_length=100)
    x_position: float = 0.0
    y_position: float = 0.0
    direction: float = Field(default=90.0, ge=0, le=360)
    size: float = Field(default=100.0, ge=0)
    is_visible: bool = True
    rotation_style: str = "all around"
    layer_order: int = 0
    draggable: bool = False


class SpriteCreate(SpriteBase):
    """Schema for creating a sprite"""
    project_id: int
    properties: Optional[Dict[str, Any]] = {}
    
    @validator('rotation_style')
    def validate_rotation_style(cls, v):
        allowed = ['all around', 'left-right', "don't rotate"]
        if v not in allowed:
            raise ValueError(f'rotation_style must be one of {allowed}')
        return v


class SpriteUpdate(BaseModel):
    """Schema for updating a sprite"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    x_position: Optional[float] = None
    y_position: Optional[float] = None
    direction: Optional[float] = Field(None, ge=0, le=360)
    size: Optional[float] = Field(None, ge=0)
    is_visible: Optional[bool] = None
    rotation_style: Optional[str] = None
    layer_order: Optional[int] = None
    current_costume_id: Optional[int] = None
    draggable: Optional[bool] = None
    properties: Optional[Dict[str, Any]] = None


class Sprite(SpriteBase):
    """Schema for sprite response"""
    id: int
    project_id: int
    current_costume_id: Optional[int] = None
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SpriteWithCostumes(Sprite):
    """Sprite with costumes included"""
    costumes: List['Costume'] = []


class SpriteComplete(SpriteWithCostumes):
    """Complete sprite with costumes, variables, and lists"""
    variables: List['SpriteVariable'] = []
    lists: List['SpriteList'] = []


# ============================================================================
# COSTUME SCHEMAS
# ============================================================================

class CostumeBase(BaseModel):
    """Base costume schema"""
    name: str = Field(..., min_length=1, max_length=100)
    costume_order: int = 0


class CostumeCreate(CostumeBase):
    """Schema for creating a costume"""
    sprite_id: int
    image_url: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded
    mime_type: str = "image/png"
    width: Optional[int] = None
    height: Optional[int] = None
    center_x: int = 0
    center_y: int = 0
    bitmap_resolution: int = 1


class CostumeUpdate(BaseModel):
    """Schema for updating a costume"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    center_x: Optional[int] = None
    center_y: Optional[int] = None
    costume_order: Optional[int] = None


class Costume(CostumeBase):
    """Schema for costume response"""
    id: int
    sprite_id: int
    image_url: Optional[str] = None
    mime_type: str
    width: Optional[int] = None
    height: Optional[int] = None
    center_x: int
    center_y: int
    bitmap_resolution: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# BACKDROP SCHEMAS
# ============================================================================

class BackdropBase(BaseModel):
    """Base backdrop schema"""
    name: str = Field(..., min_length=1, max_length=100)
    backdrop_order: int = 0


class BackdropCreate(BackdropBase):
    """Schema for creating a backdrop"""
    project_id: int
    image_url: Optional[str] = None
    image_data: Optional[str] = None
    mime_type: str = "image/png"
    width: int = 480
    height: int = 360


class BackdropUpdate(BaseModel):
    """Schema for updating a backdrop"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    backdrop_order: Optional[int] = None


class Backdrop(BackdropBase):
    """Schema for backdrop response"""
    id: int
    project_id: int
    image_url: Optional[str] = None
    mime_type: str
    width: int
    height: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# STAGE SETTINGS SCHEMAS
# ============================================================================

class StageSettingBase(BaseModel):
    """Base stage setting schema"""
    width: int = Field(default=480, ge=100, le=2000)
    height: int = Field(default=360, ge=100, le=2000)
    tempo: int = Field(default=60, ge=20, le=500)
    volume: int = Field(default=100, ge=0, le=100)
    video_state: str = "off"
    video_transparency: int = Field(default=50, ge=0, le=100)
    text_to_speech_language: str = "en"
    fps: int = Field(default=30, ge=1, le=120)
    coordinate_system: str = "center"


class StageSettingCreate(StageSettingBase):
    """Schema for creating stage settings"""
    project_id: int
    current_backdrop_id: Optional[int] = None
    settings: Optional[Dict[str, Any]] = {}


class StageSettingUpdate(BaseModel):
    """Schema for updating stage settings"""
    width: Optional[int] = Field(None, ge=100, le=2000)
    height: Optional[int] = Field(None, ge=100, le=2000)
    current_backdrop_id: Optional[int] = None
    tempo: Optional[int] = Field(None, ge=20, le=500)
    volume: Optional[int] = Field(None, ge=0, le=100)
    video_state: Optional[str] = None
    video_transparency: Optional[int] = Field(None, ge=0, le=100)
    text_to_speech_language: Optional[str] = None
    fps: Optional[int] = Field(None, ge=1, le=120)
    coordinate_system: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class StageSetting(StageSettingBase):
    """Schema for stage setting response"""
    id: int
    project_id: int
    current_backdrop_id: Optional[int] = None
    settings: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StageComplete(BaseModel):
    """Complete stage data with all elements"""
    stage_settings: StageSetting
    current_backdrop: Optional[Backdrop] = None
    sprites: List[Sprite] = []
    backdrops: List[Backdrop] = []


# ============================================================================
# SPRITE VARIABLE SCHEMAS
# ============================================================================

class SpriteVariableBase(BaseModel):
    """Base variable schema"""
    name: str = Field(..., min_length=1, max_length=100)
    value: str = "0"
    is_cloud_variable: bool = False
    is_visible: bool = False


class SpriteVariableCreate(SpriteVariableBase):
    """Schema for creating a variable"""
    project_id: int
    sprite_id: Optional[int] = None  # NULL for global variables
    x_position: int = 10
    y_position: int = 10


class SpriteVariableUpdate(BaseModel):
    """Schema for updating a variable"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[str] = None
    is_visible: Optional[bool] = None
    x_position: Optional[int] = None
    y_position: Optional[int] = None


class SpriteVariable(SpriteVariableBase):
    """Schema for variable response"""
    id: int
    project_id: int
    sprite_id: Optional[int] = None
    x_position: int
    y_position: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# SPRITE LIST SCHEMAS
# ============================================================================

class SpriteListBase(BaseModel):
    """Base list schema"""
    name: str = Field(..., min_length=1, max_length=100)
    items: List[str] = []
    is_visible: bool = False


class SpriteListCreate(SpriteListBase):
    """Schema for creating a list"""
    project_id: int
    sprite_id: Optional[int] = None
    width: int = 100
    height: int = 200
    x_position: int = 10
    y_position: int = 10


class SpriteListUpdate(BaseModel):
    """Schema for updating a list"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    items: Optional[List[str]] = None
    is_visible: Optional[bool] = None
    width: Optional[int] = None
    height: Optional[int] = None
    x_position: Optional[int] = None
    y_position: Optional[int] = None


class SpriteList(SpriteListBase):
    """Schema for list response"""
    id: int
    project_id: int
    sprite_id: Optional[int] = None
    width: int
    height: int
    x_position: int
    y_position: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# LIBRARY SCHEMAS
# ============================================================================

class LibrarySpriteBase(BaseModel):
    """Base library sprite schema"""
    name: str
    description: Optional[str] = None
    category: str
    tags: List[str] = []


class LibrarySprite(LibrarySpriteBase):
    """Schema for library sprite response"""
    id: int
    thumbnail_url: Optional[str] = None
    sprite_data: Dict[str, Any]
    author: Optional[str] = None
    is_official: bool
    download_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class LibraryBackdropBase(BaseModel):
    """Base library backdrop schema"""
    name: str
    description: Optional[str] = None
    category: str
    tags: List[str] = []


class LibraryBackdrop(LibraryBackdropBase):
    """Schema for library backdrop response"""
    id: int
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    width: int
    height: int
    author: Optional[str] = None
    is_official: bool
    download_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ACTION SCHEMAS (for sprite operations)
# ============================================================================

class MoveSpriteRequest(BaseModel):
    """Request to move sprite"""
    x_position: float
    y_position: float


class RotateSpriteRequest(BaseModel):
    """Request to rotate sprite"""
    direction: float = Field(..., ge=0, le=360)


class SizeSpriteRequest(BaseModel):
    """Request to change sprite size"""
    size: float = Field(..., ge=0)


class VisibilityRequest(BaseModel):
    """Request to change visibility"""
    is_visible: bool


class SetCostumeRequest(BaseModel):
    """Request to set active costume"""
    costume_id: int


class SetBackdropRequest(BaseModel):
    """Request to set active backdrop"""
    backdrop_id: int


class LayerReorderRequest(BaseModel):
    """Request to reorder sprite layers"""
    sprite_orders: List[Dict[str, int]]  # [{"sprite_id": 1, "layer_order": 0}, ...]


class SpeechBubbleRequest(BaseModel):
    """Request to show speech bubble"""
    text: str
    duration: Optional[int] = 2  # seconds
    bubble_type: str = "say"  # "say" or "think"


# ============================================================================
# COLLISION SCHEMAS
# ============================================================================

class CollisionResponse(BaseModel):
    """Response for collision check"""
    colliding: bool
    sprites: List[int] = []  # IDs of colliding sprites


class EdgeTouchResponse(BaseModel):
    """Response for edge touch check"""
    touching: bool
    edge: Optional[str] = None  # "top", "bottom", "left", "right"


# ============================================================================
# BULK OPERATIONS
# ============================================================================

class BulkSpriteDelete(BaseModel):
    """Request to delete multiple sprites"""
    sprite_ids: List[int]


class BulkCostumeDelete(BaseModel):
    """Request to delete multiple costumes"""
    costume_ids: List[int]


# Update forward references
SpriteWithCostumes.model_rebuild()
SpriteComplete.model_rebuild()
