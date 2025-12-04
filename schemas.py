"""
Pydantic Schemas for API Request/Response Validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime
from models import UserRole, ProjectStatus, AssetType
from enum import Enum as PyEnum
from typing import Optional
from pydantic import BaseModel, Field, conint, confloat

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
    current_message: Optional[str] = Field(None, description="The current message being said or thought.")
    message_duration: Optional[float] = Field(None, description="The remaining duration of the message.")
    message_type: Optional[str] = Field(None, description="The type of message ('say' or 'think').")
    current_costume_id: Optional[int] = None
    current_costume_name: Optional[str] = None
    graphic_effects: Optional[Dict[str, float]] = Field(None, description="Map of graphic effects and their values.") 

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
    sprite_id: Optional[int] = None  
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


# ============================================================================
# MOTION BLOCKS
# ============================================================================

from enum import Enum as PyEnum

# Enum for Rotation Style
class RotationStyle(str, PyEnum):
    ALL_AROUND = "all_around"
    LEFT_RIGHT = "left_right"
    DONT_ROTATE = "dont_rotate"

# Enum for Motion Targets (random position, mouse-pointer, other sprites)
class MotionTarget(str, PyEnum):
    RANDOM_POSITION = "random_position"
    MOUSE_POINTER = "mouse-pointer"
    # Additional logic needed for other sprite targets (target should be sprite ID)

from enum import Enum as PyEnum

# Enum for Rotation Style
class RotationStyle(str, PyEnum):
    ALL_AROUND = "all_around"
    LEFT_RIGHT = "left_right"
    DONT_ROTATE = "dont_rotate"

# Enum for Motion Targets (random position, mouse-pointer, other sprites)
class MotionTarget(str, PyEnum):
    RANDOM_POSITION = "random_position"
    MOUSE_POINTER = "mouse-pointer"
    # Additional logic needed for other sprite targets (target should be sprite ID)


class MotionMove(BaseModel):
    """Payload for 'move steps'"""
    steps: float = Field(10.0, description="Number of steps to move in the current direction.")

class MotionTurn(BaseModel):
    """Payload for 'turn degrees'"""
    degrees: float = Field(15.0, description="Degrees to turn (clockwise or counter-clockwise).")

class MotionGoToTarget(BaseModel):
    """Payload for 'go to target' (e.g., random position, mouse-pointer)"""
    target: MotionTarget = Field(MotionTarget.RANDOM_POSITION, description="Target type to go to.")

class MotionGoToPayload(BaseModel):
    """Combined Payload for go to x:y:, go to random, or go to mouse-pointer"""
    target: Optional[MotionTarget] = Field(None, description="Target (random_position, mouse-pointer, or None for x/y).")
    x: Optional[float] = None
    y: Optional[float] = None

class MotionGlide(BaseModel):
    """Payload for 'glide secs to target/x:y:'"""
    secs: float = Field(1.0, gt=0, description="Duration in seconds for the glide animation.")
    target: Optional[MotionTarget] = Field(None, description="Target type for glide (random_position or x/y if None).")
    x: Optional[float] = None
    y: Optional[float] = None

class MotionPointDirection(BaseModel):
    """Payload for 'point in direction'"""
    direction: float = Field(90.0, ge=-180, le=360, description="Direction in degrees (typically 0-360).")

class MotionPointTowardsTarget(BaseModel):
    """Payload for 'point towards target'"""
    target: MotionTarget = Field(MotionTarget.MOUSE_POINTER, description="Target to point towards.")

class MotionChangePosition(BaseModel):
    """Payload for 'change x/y by'"""
    change: float = Field(10.0, description="Amount to change the x or y position by.")

class MotionSetPosition(BaseModel):
    """Payload for 'set x/y to'"""
    value: float = Field(0.0, description="Value to set the x or y position to.")

class MotionSetRotationStyle(BaseModel):
    """Payload for 'set rotation style'"""
    rotation_style: RotationStyle = Field(RotationStyle.LEFT_RIGHT, description="Rotation style enum.")

class MotionPointTowardsPayload(BaseModel):
    """Payload for 'point towards target', including optional coordinates for mouse-pointer."""
    target: str = Field(..., description="Target type (e.g., 'mouse-pointer' or 'sprite-2')")
    x: Optional[float] = None
    y: Optional[float] = None

# --- Reporter Block Response Schemas ---

class MotionPositionValue(BaseModel):
    """Response model for X Position, Y Position, Direction reporter blocks"""
    value: float
    
    class Config:
        from_attributes = True

# --- Looks Block Enums ---

class LookMessageAction(str, PyEnum):
    SAY = "say"
    THINK = "think"

class LookEffect(str, PyEnum):
    COLOR = "color"
    FISHEYE = "fisheye"
    WHIRL = "whirl"
    PIXELATE = "pixelate"
    MOSAIC = "mosaic"
    BRIGHTNESS = "brightness"
    GHOST = "ghost"

class LookLayer(str, PyEnum):
    FRONT = "front"
    BACK = "back"

# -
# -- Looks Block Payloads ---

class LookSayThink(BaseModel):
    """Payload for 'say/think' blocks with duration."""
    message: str = Field("Hello!", description="The text the sprite should say or think.")
    secs: Optional[float] = Field(None, gt=0, description="Duration in seconds (Optional for permanent say/think).")

class LookChangeSize(BaseModel):
    """Payload for 'change size by' block."""
    change: float = Field(10.0, description="The amount to change the size by.")

class LookSwitchCostumePayload(BaseModel):
    """
    Payload for 'switch costume to' block. 
    Uses 'target' field to match expected input structure.
    """
    target: str = Field(..., description="The name of the costume to switch to.")    

# class LookSetSize(BaseModel):
#     """Payload for 'set size to' block."""
#     percent: confloat(gt=0) = Field(100.0, description="The percentage of the original size.")

class LookSetSize(BaseModel):
    """Payload for 'set size to' block."""
    percent: Annotated[float, confloat(gt=0)] = Field(100.0, description="The percentage of the original size.")

class LookChangeEffect(BaseModel):
    """Payload for 'change effect by' block."""
    effect: LookEffect = Field(LookEffect.COLOR, description="The graphic effect to change.")
    change: float = Field(25.0, description="The amount to change the effect by.")

class LookSetEffect(BaseModel):
    """Payload for 'set effect to' block."""
    effect: LookEffect = Field(LookEffect.COLOR, description="The graphic effect to set.")
    value: float = Field(0.0, description="The value to set the effect to.")

class LookGoToLayer(BaseModel):
    """Payload for 'go to front/back layer' block."""
    layer: LookLayer = Field(LookLayer.FRONT, description="The layer to move the sprite to.")

class LookChangeLayer(BaseModel):
    """Payload for 'go forward/backward layers' block."""
    forward_layers: int = Field(1, description="Number of layers to move forward/backward.")

# --- Reporter Block Response Schemas ---

class LookReporterValue(BaseModel):
    """Generic response for reporter blocks (costume, backdrop, size)."""
    value: float


"""
Add these Event System schemas to your existing schemas.py file
Append after your existing sprite schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============================================================================
# EVENT ENUMS
# ============================================================================

class EventType(str, Enum):
    """Types of events that can be triggered"""
    WHEN_CLICKED = "when_clicked"
    WHEN_KEY_PRESSED = "when_key_pressed"
    WHEN_SPRITE_CLICKED = "when_sprite_clicked"
    WHEN_BACKDROP_SWITCHES = "when_backdrop_switches"
    WHEN_GREATER_THAN = "when_greater_than"
    WHEN_BROADCAST_RECEIVED = "when_broadcast_received"
    WHEN_I_START_AS_CLONE = "when_i_start_as_clone"


class KeyType(str, Enum):
    """Keyboard keys that can trigger events"""
    SPACE = "space"
    UP_ARROW = "up arrow"
    DOWN_ARROW = "down arrow"
    RIGHT_ARROW = "right arrow"
    LEFT_ARROW = "left arrow"
    ANY = "any"
    # Letters
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"
    # Numbers
    NUM_0 = "0"
    NUM_1 = "1"
    NUM_2 = "2"
    NUM_3 = "3"
    NUM_4 = "4"
    NUM_5 = "5"
    NUM_6 = "6"
    NUM_7 = "7"
    NUM_8 = "8"
    NUM_9 = "9"


class SensorType(str, Enum):
    """Sensor types for 'when greater than' blocks"""
    LOUDNESS = "loudness"
    TIMER = "timer"
    VIDEO_MOTION = "video motion"


class BroadcastScope(str, Enum):
    """Scope of broadcast messages"""
    PROJECT = "project"  # All sprites in project
    SPRITE = "sprite"  # Specific sprite only
    GLOBAL = "global"  # All projects (for multiplayer)


# ============================================================================
# EVENT HANDLER SCHEMAS
# ============================================================================

class EventHandlerBase(BaseModel):
    """Base schema for event handlers"""
    event_type: EventType
    is_enabled: bool = True
    execution_order: int = 0  # Order of execution if multiple handlers


class WhenClickedHandler(EventHandlerBase):
    """Handler for 'when green flag clicked' event"""
    event_type: EventType = EventType.WHEN_CLICKED


class WhenKeyPressedHandler(EventHandlerBase):
    """Handler for 'when [key] pressed' event"""
    event_type: EventType = EventType.WHEN_KEY_PRESSED
    key: KeyType
   
    @validator('key')
    def validate_key(cls, v):
        if v not in KeyType.__members__.values():
            raise ValueError(f'Invalid key: {v}')
        return v


class WhenSpriteClickedHandler(EventHandlerBase):
    """Handler for 'when this sprite clicked' event"""
    event_type: EventType = EventType.WHEN_SPRITE_CLICKED
    sprite_id: int


class WhenBackdropSwitchesHandler(EventHandlerBase):
    """Handler for 'when backdrop switches to [backdrop]' event"""
    event_type: EventType = EventType.WHEN_BACKDROP_SWITCHES
    backdrop_id: Optional[int] = None  # None = any backdrop
    backdrop_name: Optional[str] = None


class WhenGreaterThanHandler(EventHandlerBase):
    """Handler for 'when [sensor] > [value]' event"""
    event_type: EventType = EventType.WHEN_GREATER_THAN
    sensor_type: SensorType
    threshold_value: float


class WhenBroadcastReceivedHandler(EventHandlerBase):
    """Handler for 'when I receive [message]' event"""
    event_type: EventType = EventType.WHEN_BROADCAST_RECEIVED
    message_name: str


# ----------------------------------------------------------------------------
# EVENTS BLOCKS SCHEMAS
# ----------------------------------------------------------------------------

# For creating new messages that can be broadcast
class MessageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class MessageCreate(MessageBase):
    project_id: int

class Message(MessageBase):
    id: int
    project_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# For the broadcast block API request
class BroadcastRequest(BaseModel):
    message_name: str = Field(..., description="The name of the message to broadcast")
    wait: bool = Field(False, description="Whether to wait for receivers to finish (used for 'broadcast and wait')")


# --- Add this new schema to schemas.py ---

class SensorDataReport(BaseModel):
    project_id: int
    sensor_name: str = Field(..., description="e.g., loudness, timer, video_motion")
    value: float
    sprite_id: Optional[int] = None    

# # ============================================================================
# # EVENT BINDING SCHEMAS (Link handlers to sprites/scripts)
# # ============================================================================

# class EventBindingBase(BaseModel):
#     """Base schema for event bindings"""
#     sprite_id: Optional[int] = None  # None for stage events
#     project_id: int
#     handler_data: Dict[str, Any]  # JSON data for the specific handler
#     script_blocks: Optional[List[Dict[str, Any]]] = []  # Blockly blocks to execute
#     is_active: bool = True


# class EventBindingCreate(EventBindingBase):
#     """Schema for creating event binding"""
#     pass


# class EventBindingUpdate(BaseModel):
#     """Schema for updating event binding"""
#     handler_data: Optional[Dict[str, Any]] = None
#     script_blocks: Optional[List[Dict[str, Any]]] = None
#     is_active: Optional[bool] = None
#     execution_order: Optional[int] = None


# class EventBinding(EventBindingBase):
#     """Schema for event binding response"""
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime] = None

#     class Config:
#         from_attributes = True


# # ============================================================================
# # BROADCAST MESSAGE SCHEMAS
# # ============================================================================

# class BroadcastMessageBase(BaseModel):
#     """Base schema for broadcast messages"""
#     name: str = Field(..., min_length=1, max_length=100)
#     scope: BroadcastScope = BroadcastScope.PROJECT


# class BroadcastMessageCreate(BroadcastMessageBase):
#     """Schema for creating broadcast message"""
#     project_id: int
#     description: Optional[str] = None


# class BroadcastMessageUpdate(BaseModel):
#     """Schema for updating broadcast message"""
#     name: Optional[str] = Field(None, min_length=1, max_length=100)
#     description: Optional[str] = None
#     scope: Optional[BroadcastScope] = None


# class BroadcastMessage(BroadcastMessageBase):
#     """Schema for broadcast message response"""
#     id: int
#     project_id: int
#     description: Optional[str] = None
#     created_at: datetime
#     updated_at: Optional[datetime] = None

#     class Config:
#         from_attributes = True


# # ============================================================================
# # EVENT EXECUTION SCHEMAS (Runtime)
# # ============================================================================

# class TriggerEventRequest(BaseModel):
#     """Request to trigger an event"""
#     event_type: EventType
#     event_data: Dict[str, Any] = {}  # Additional event data
   
#     # Examples of event_data:
#     # - For key_pressed: {"key": "space"}
#     # - For sprite_clicked: {"sprite_id": 123}
#     # - For backdrop_switches: {"backdrop_id": 456}
#     # - For broadcast: {"message": "start game"}
#     # - For greater_than: {"sensor": "loudness", "value": 50}


# class ExecuteScriptRequest(BaseModel):
#     """Request to execute a script from event"""
#     event_binding_id: int
#     context: Optional[Dict[str, Any]] = {}  # Runtime context (variables, etc.)


# class EventExecutionResult(BaseModel):
#     """Result of event execution"""
#     event_binding_id: int
#     success: bool
#     output: Optional[str] = None
#     error: Optional[str] = None
#     execution_time: float
#     variables_changed: Dict[str, Any] = {}


# class BroadcastRequest(BaseModel):
#     """Request to broadcast a message"""
#     message_name: str
#     wait: bool = False  # If True, wait for all handlers to complete
#     data: Optional[Dict[str, Any]] = {}  # Additional data to send


# class BroadcastAndWaitRequest(BroadcastRequest):
#     """Request to broadcast and wait"""
#     wait: bool = True


# # ============================================================================
# # EVENT LOG SCHEMAS (for debugging/analytics)
# # ============================================================================

# class EventLogBase(BaseModel):
#     """Base schema for event logs"""
#     event_type: EventType
#     event_data: Dict[str, Any]


# class EventLog(EventLogBase):
#     """Schema for event log response"""
#     id: int
#     project_id: int
#     sprite_id: Optional[int] = None
#     user_id: int
#     triggered_at: datetime
#     handlers_executed: int
#     execution_time: float

#     class Config:
#         from_attributes = True


# # ============================================================================
# # KEY PRESS DETECTION SCHEMAS
# # ============================================================================

# class KeyPressEvent(BaseModel):
#     """Schema for key press event"""
#     key: KeyType
#     timestamp: datetime = Field(default_factory=datetime.utcnow)
#     is_pressed: bool = True


# class KeyReleaseEvent(BaseModel):
#     """Schema for key release event"""
#     key: KeyType
#     timestamp: datetime = Field(default_factory=datetime.utcnow)
#     is_pressed: bool = False


# class KeyboardState(BaseModel):
#     """Schema for current keyboard state"""
#     pressed_keys: List[KeyType] = []
#     last_key: Optional[KeyType] = None
#     last_press_time: Optional[datetime] = None


# # ============================================================================
# # MOUSE/CLICK EVENT SCHEMAS
# # ============================================================================

# class MouseClickEvent(BaseModel):
#     """Schema for mouse click event"""
#     x: float
#     y: float
#     timestamp: datetime = Field(default_factory=datetime.utcnow)
#     button: str = "left"  # left, right, middle


# class SpriteClickEvent(BaseModel):
#     """Schema for sprite click event"""
#     sprite_id: int
#     x: float  # Click position relative to sprite
#     y: float
#     timestamp: datetime = Field(default_factory=datetime.utcnow)


# # ============================================================================
# # TIMER SCHEMAS
# # ============================================================================

# class TimerState(BaseModel):
#     """Schema for timer state"""
#     project_id: int
#     current_value: float  # Seconds since start
#     is_running: bool = True
#     started_at: datetime


# class ResetTimerRequest(BaseModel):
#     """Request to reset timer"""
#     project_id: int


# # ============================================================================
# # SENSOR SCHEMAS (for when greater than blocks)
# # ============================================================================

# class SensorReading(BaseModel):
#     """Schema for sensor reading"""
#     sensor_type: SensorType
#     value: float
#     timestamp: datetime = Field(default_factory=datetime.utcnow)


# class LoudnessReading(SensorReading):
#     """Schema for loudness sensor reading"""
#     sensor_type: SensorType = SensorType.LOUDNESS
#     value: float = Field(..., ge=0, le=100)  # 0-100


# class TimerReading(SensorReading):
#     """Schema for timer reading"""
#     sensor_type: SensorType = SensorType.TIMER


# class VideoMotionReading(SensorReading):
#     """Schema for video motion reading"""
#     sensor_type: SensorType = SensorType.VIDEO_MOTION
#     value: float = Field(..., ge=0, le=100)
#     sprite_id: Optional[int] = None  # Motion on specific sprite


# # ============================================================================
# # CLONE EVENT SCHEMAS
# # ============================================================================

# class CloneCreatedEvent(BaseModel):
#     """Schema for clone creation event"""
#     original_sprite_id: int
#     clone_sprite_id: int
#     timestamp: datetime = Field(default_factory=datetime.utcnow)


# class CloneDeletedEvent(BaseModel):
#     """Schema for clone deletion event"""
#     clone_sprite_id: int
#     timestamp: datetime = Field(default_factory=datetime.utcnow)


# # ============================================================================
# # EVENT STATISTICS SCHEMAS
# # ============================================================================

# class EventStatistics(BaseModel):
#     """Schema for event statistics"""
#     project_id: int
#     total_events_triggered: int
#     events_by_type: Dict[EventType, int]
#     most_triggered_event: Optional[EventType] = None
#     average_execution_time: float
#     total_broadcasts_sent: int


# # ============================================================================
# # COMPLETE EVENT RESPONSE SCHEMAS
# # ============================================================================

# class ProjectEventsComplete(BaseModel):
#     """Complete event data for a project"""
#     project_id: int
#     event_bindings: List[EventBinding]
#     broadcast_messages: List[BroadcastMessage]
#     keyboard_state: Optional[KeyboardState] = None
#     timer_state: Optional[TimerState] = None


# class SpriteEventsComplete(BaseModel):
#     """Complete event data for a sprite"""
#     sprite_id: int
#     event_bindings: List[EventBinding]
#     active_handlers: List[str]     