"""
Database Models for Blockly Platform
SQLAlchemy ORM Models
"""

from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    USER = "user"


class ProjectStatus(str, enum.Enum):
    """Project status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AssetType(str, enum.Enum):
    """Asset type enumeration"""
    SPRITE = "sprite"
    BACKDROP = "backdrop"
    SOUND = "sound"
    COSTUME = "costume"
    IMAGE = "image"
    VIDEO = "video"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String(255))
    bio = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="user", cascade="all, delete-orphan")
    shared_projects = relationship("ProjectShare", back_populates="shared_with_user")


class Project(Base):
    """Project model - stores Blockly workspace data"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Blockly workspace XML/JSON
    workspace_xml = Column(Text)  # Blockly workspace XML
    workspace_json = Column(JSON)  # Alternative JSON format
    
    # Generated code
    generated_code = Column(Text)  # Generated Python/JS code
    code_language = Column(String(20), default="python")  # python, javascript, etc.
    
    # Project metadata
    thumbnail_url = Column(String(255))
    is_public = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)
    
    # Version control
    version = Column(Integer, default=1)
    parent_project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # For cloned projects
    
    # Statistics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    fork_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="project")
    shared_with = relationship("ProjectShare", back_populates="project")
    children = relationship("Project", remote_side=[parent_project_id])
    sprites = relationship("Sprite", back_populates="project", cascade="all, delete-orphan")
    backdrops = relationship("Backdrop", back_populates="project", cascade="all, delete-orphan")
    stage_setting = relationship("StageSetting", back_populates="project", uselist=False, cascade="all, delete-orphan")


class Asset(Base):
    """Asset model - sprites, sounds, backdrops, etc."""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False)
    
    # File storage
    file_url = Column(String(500))  # URL to stored file (S3, local, etc.)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String(100))
    
    # Asset data (for small assets can be stored directly)
    data_base64 = Column(Text)  # Base64 encoded data
    
    # Asset properties
    properties = Column(JSON)  # Store sprite properties, sound properties, etc.
    
    # Metadata
    width = Column(Integer)  # For images/sprites
    height = Column(Integer)  # For images/sprites
    duration = Column(Float)  # For sounds/videos
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="assets")


class ExecutionLog(Base):
    """Execution log - stores code execution history"""
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Execution details
    code = Column(Text, nullable=False)
    language = Column(String(20), nullable=False)
    
    # Results
    output = Column(Text)
    error = Column(Text)
    execution_time = Column(Float)  # Execution time in seconds
    exit_code = Column(Integer, default=0)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    
    # Timestamp
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="execution_logs")
    project = relationship("Project", back_populates="execution_logs")


class ProjectShare(Base):
    """Project sharing model - for collaboration"""
    __tablename__ = "project_shares"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Permissions
    can_edit = Column(Boolean, default=False)
    can_view = Column(Boolean, default=True)
    can_execute = Column(Boolean, default=True)
    
    # Timestamps
    shared_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="shared_with")
    shared_with_user = relationship("User", back_populates="shared_projects")


class Extension(Base):
    """Custom extensions/blocks model"""
    __tablename__ = "extensions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Extension code
    block_definitions = Column(JSON)  # Block definitions in JSON
    generator_code = Column(Text)  # Code generator functions
    
    # Metadata
    version = Column(String(20), default="1.0.0")
    author = Column(String(100))
    icon_url = Column(String(255))
    category = Column(String(50))  # AI, IoT, Robotics, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    is_official = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class HardwareDevice(Base):
    """Connected hardware devices (Arduino, ESP32, sensors, etc.)"""
    __tablename__ = "hardware_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # arduino, esp32, microbit, etc.
    serial_number = Column(String(100))
    
    # Connection details
    port = Column(String(50))
    baud_rate = Column(Integer)
    is_connected = Column(Boolean, default=False)
    
    # Device info
    firmware_version = Column(String(50))
    capabilities = Column(JSON)  # Supported sensors, actuators, etc.
    
    # Timestamps
    last_connected_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())



    """
Add these models to your existing models.py file
Append after your existing models (User, Project, Asset, etc.)
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


# ============================================================================
# ENUMS
# ============================================================================

class RotationStyle(str, enum.Enum):
    """Sprite rotation styles"""
    ALL_AROUND = "all around"
    LEFT_RIGHT = "left-right"
    DONT_ROTATE = "don't rotate"


class CoordinateSystem(str, enum.Enum):
    """Stage coordinate system"""
    CENTER = "center"  # Scratch-style: -240 to 240
    CORNER = "corner"  # Top-left origin: 0,0


class VideoState(str, enum.Enum):
    """Video state for stage"""
    ON = "on"
    OFF = "off"
    ON_FLIPPED = "on-flipped"


# ============================================================================
# SPRITE MODEL
# ============================================================================

class Sprite(Base):
    """Sprite model - visual characters/objects in projects"""
    __tablename__ = "sprites"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Basic properties
    name = Column(String(100), nullable=False)
    
    # Position and appearance
    x_position = Column(Float, default=0.0)
    y_position = Column(Float, default=0.0)
    direction = Column(Float, default=90.0)  # 0-360 degrees, 90 = right
    size = Column(Float, default=100.0)  # Percentage (100 = normal size)
    
    # Visibility
    is_visible = Column(Boolean, default=True)
    
    # Rotation
    rotation_style = Column(String(20), default=RotationStyle.ALL_AROUND.value)
    
    # Layer ordering (z-index)
    layer_order = Column(Integer, default=0)
    
  
    # Current costume
    current_costume_id = Column(Integer, nullable=True)
    
    # Interactivity
    draggable = Column(Boolean, default=False)

    graphic_effects = Column(JSON, default={})
    
    # Custom properties (for extensions, effects, etc.)
    properties = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    
    # Relationships
    project = relationship("Project", back_populates="sprites")
    costumes = relationship("Costume", back_populates="sprite", cascade="all, delete-orphan", order_by="Costume.costume_order")
    variables = relationship("SpriteVariable", back_populates="sprite", cascade="all, delete-orphan")
    lists = relationship("SpriteList", back_populates="sprite", cascade="all, delete-orphan")


# ============================================================================
# COSTUME MODEL
# ============================================================================

class Costume(Base):
    """Costume model - different appearances/looks for sprites"""
    __tablename__ = "costumes"

    id = Column(Integer, primary_key=True, index=True)
    sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=False)
    
    # Basic info
    name = Column(String(100), nullable=False)
    
    # Image storage (either URL or base64 data)
    image_url = Column(String(500))  # External URL (S3, CDN, etc.)
    image_data = Column(Text)  # Base64 encoded image (for small images)
    mime_type = Column(String(50), default="image/png")
    
    # Image dimensions
    width = Column(Integer)
    height = Column(Integer)
    
    # Rotation center point
    center_x = Column(Integer, default=0)  # Relative to top-left
    center_y = Column(Integer, default=0)
    
    # Bitmap resolution
    bitmap_resolution = Column(Integer, default=1)
    
    # Order in costume list
    costume_order = Column(Integer, default=0)

    # current_costume_id = Column(Integer, nullable=True)
    # # ADD THIS LINE:
    # current_costume_name = Column(String(100), nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sprite = relationship("Sprite", back_populates="costumes")


# ============================================================================
# BACKDROP MODEL
# ============================================================================

class Backdrop(Base):
    """Backdrop model - stage backgrounds"""
    __tablename__ = "backdrops"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # Basic info
    name = Column(String(100), nullable=False)
    
    # Image storage
    image_url = Column(String(500))
    image_data = Column(Text)  # Base64
    mime_type = Column(String(50), default="image/png")
    
    # Dimensions
    width = Column(Integer, default=480)
    height = Column(Integer, default=360)
    
    # Order
    backdrop_order = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="backdrops")


# ============================================================================
# STAGE SETTINGS MODEL
# ============================================================================

class StageSetting(Base):
    """Stage settings - configuration for project stage/canvas"""
    __tablename__ = "stage_settings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    # Canvas dimensions
    width = Column(Integer, default=480)
    height = Column(Integer, default=360)
    
    # Current backdrop
    current_backdrop_id = Column(Integer, ForeignKey("backdrops.id"), nullable=True)
    
    # Audio settings
    tempo = Column(Integer, default=60)  # BPM
    volume = Column(Integer, default=100)  # 0-100
    
    # Video settings
    video_state = Column(String(20), default=VideoState.OFF.value)
    video_transparency = Column(Integer, default=50)  # 0-100
    
    # Language
    text_to_speech_language = Column(String(20), default="en")
    
    # Performance
    fps = Column(Integer, default=30)  # Frames per second
    
    # Coordinate system
    coordinate_system = Column(String(20), default=CoordinateSystem.CENTER.value)
    
    # Additional settings
    settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="stage_setting", uselist=False)
    current_backdrop = relationship("Backdrop", foreign_keys=[current_backdrop_id])


# ============================================================================
# SPRITE VARIABLE MODEL
# ============================================================================

class SpriteVariable(Base):
    """Variables for sprites or global project variables"""
    __tablename__ = "sprite_variables"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=True)  # NULL = global variable
    
    # Variable info
    name = Column(String(100), nullable=False)
    value = Column(Text, default="0")
    
    # Cloud variable (syncs across users)
    is_cloud_variable = Column(Boolean, default=False)
    
    # Display on stage
    is_visible = Column(Boolean, default=False)
    x_position = Column(Integer, default=10)
    y_position = Column(Integer, default=10)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project")
    sprite = relationship("Sprite", back_populates="variables")


# ============================================================================
# SPRITE LIST MODEL
# ============================================================================

class SpriteList(Base):
    """Lists for sprites or global project lists"""
    __tablename__ = "sprite_lists"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=True)  # NULL = global list
    
    # List info
    name = Column(String(100), nullable=False)
    items = Column(JSON, default=[])  # Array of items
    
    # Display on stage
    is_visible = Column(Boolean, default=False)
    width = Column(Integer, default=100)
    height = Column(Integer, default=200)
    x_position = Column(Integer, default=10)
    y_position = Column(Integer, default=10)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project")
    sprite = relationship("Sprite", back_populates="lists")


# ============================================================================
# LIBRARY SPRITE MODEL (Pre-made sprites)
# ============================================================================

class LibrarySprite(Base):
    """Pre-made sprites available in the library"""
    __tablename__ = "library_sprites"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # Animals, People, Fantasy, etc.
    tags = Column(JSON, default=[])  # Searchable tags
    
    # Preview image
    thumbnail_url = Column(String(500))
    
    # Sprite data (JSON with costumes, etc.)
    sprite_data = Column(JSON)
    
    # Metadata
    author = Column(String(100))
    is_official = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ============================================================================
# LIBRARY BACKDROP MODEL (Pre-made backdrops)
# ============================================================================

class LibraryBackdrop(Base):
    """Pre-made backdrops available in the library"""
    __tablename__ = "library_backdrops"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # Outdoors, Indoors, Space, etc.
    tags = Column(JSON, default=[])
    
    # Image
    image_url = Column(String(500))
    thumbnail_url = Column(String(500))
    width = Column(Integer, default=480)
    height = Column(Integer, default=360)
    
    # Metadata
    author = Column(String(100))
    is_official = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# # ============================================================================
# # UPDATE EXISTING PROJECT MODEL
# # Add these relationships to your existing Project model
# # ============================================================================

# """
# Add these lines to your existing Project class in models.py:

# class Project(Base):
#     # ... existing fields ...
    
#     # Add these relationships:
#     sprites = relationship("Sprite", back_populates="project", cascade="all, delete-orphan")
#     backdrops = relationship("Backdrop", back_populates="project", cascade="all, delete-orphan")
#     stage_setting = relationship("StageSetting", back_populates="project", uselist=False, cascade="all, delete-orphan")
# """


# """
# Add these Event System models to your existing models.py file
# Append after your existing sprite models
# """

# from sqlalchemy import Column, Integer, String, Float, Boolean, Text, JSON, ForeignKey, DateTime
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from database import Base


# # ============================================================================
# # EVENT BINDING MODEL
# # ============================================================================

# class EventBinding(Base):
#     """
#     Event Binding Model
#     Links events (when clicked, when key pressed, etc.) to scripts
#     """
#     __tablename__ = "event_bindings"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
#     sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=True)  # None for stage events
   
#     # Event type and configuration
#     event_type = Column(String(50), nullable=False)  # when_clicked, when_key_pressed, etc.
#     handler_data = Column(JSON, default={})  # Event-specific data (key, backdrop_id, message, etc.)
   
#     # Script to execute
#     script_blocks = Column(JSON, default=[])  # Array of Blockly blocks
   
#     # Execution settings
#     is_active = Column(Boolean, default=True)
#     execution_order = Column(Integer, default=0)  # Order if multiple handlers for same event
   
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
   
#     # Relationships
#     project = relationship("Project", back_populates="event_bindings")
#     sprite = relationship("Sprite", back_populates="event_bindings")


# # ============================================================================
# # BROADCAST MESSAGE MODEL
# # ============================================================================

# class BroadcastMessage(Base):
#     """
#     Broadcast Message Model
#     Defines custom broadcast messages for inter-sprite communication
#     """
#     __tablename__ = "broadcast_messages"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
   
#     # Message details
#     name = Column(String(100), nullable=False)
#     description = Column(Text)
#     scope = Column(String(20), default="project")  # project, sprite, global
   
#     # Timestamps
#     created_at = Column(DateTime(timezone=True), server_default=func.now())
#     updated_at = Column(DateTime(timezone=True), onupdate=func.now())
   
#     # Relationships
#     project = relationship("Project", back_populates="broadcast_messages")


# # ============================================================================
# # EVENT LOG MODEL (for analytics/debugging)
# # ============================================================================

# class EventLog(Base):
#     """
#     Event Log Model
#     Records when events are triggered for analytics and debugging
#     """
#     __tablename__ = "event_logs"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
#     sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="SET NULL"), nullable=True)
#     user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
   
#     # Event details
#     event_type = Column(String(50), nullable=False)
#     event_data = Column(JSON, default={})
   
#     # Execution results
#     handlers_executed = Column(Integer, default=0)
#     execution_time = Column(Float, default=0.0)  # Seconds
   
#     # Timestamp
#     triggered_at = Column(DateTime(timezone=True), server_default=func.now())
   
#     # Relationships
#     project = relationship("Project")
#     sprite = relationship("Sprite")
#     user = relationship("User")


# # ============================================================================
# # KEYBOARD STATE MODEL (runtime state)
# # ============================================================================

# class KeyboardState(Base):
#     """
#     Keyboard State Model
#     Tracks currently pressed keys for a project session
#     """
#     __tablename__ = "keyboard_states"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
#     session_id = Column(String(100))  # User session identifier
   
#     # Keyboard state
#     pressed_keys = Column(JSON, default=[])  # Array of currently pressed keys
#     last_key = Column(String(20))
#     last_press_time = Column(DateTime(timezone=True))
   
#     # Timestamp
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
   
#     # Relationships
#     project = relationship("Project")


# # ============================================================================
# # TIMER STATE MODEL (runtime state)
# # ============================================================================

# class TimerState(Base):
#     """
#     Timer State Model
#     Tracks timer state for projects
#     """
#     __tablename__ = "timer_states"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)
   
#     # Timer state
#     current_value = Column(Float, default=0.0)  # Current timer value in seconds
#     is_running = Column(Boolean, default=True)
#     started_at = Column(DateTime(timezone=True), server_default=func.now())
   
#     # Timestamp
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
   
#     # Relationships
#     project = relationship("Project")


# # ============================================================================
# # SENSOR READING MODEL (for "when greater than" blocks)
# # ============================================================================

# class SensorReading(Base):
#     """
#     Sensor Reading Model
#     Stores sensor readings for "when greater than" blocks
#     """
#     __tablename__ = "sensor_readings"

#     id = Column(Integer, primary_key=True, index=True)
#     project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
#     sprite_id = Column(Integer, ForeignKey("sprites.id", ondelete="CASCADE"), nullable=True)
   
#     # Sensor data
#     sensor_type = Column(String(50), nullable=False)  # loudness, timer, video_motion
#     value = Column(Float, nullable=False)
   
#     # Timestamp
#     recorded_at = Column(DateTime(timezone=True), server_default=func.now())
   
#     # Relationships
#     project = relationship("Project")
#     sprite = relationship("Sprite")


# # ============================================================================
# # UPDATE EXISTING MODELS - Add these relationships
# # ============================================================================

# """
# Add these relationships to your existing models:

# # In Project model:
# class Project(Base):
#     # ... existing fields ...
   
#     # Add these relationships:
#     event_bindings = relationship("EventBinding", back_populates="project", cascade="all, delete-orphan")
#     broadcast_messages = relationship("BroadcastMessage", back_populates="project", cascade="all, delete-orphan")


# # In Sprite model:
# class Sprite(Base):
#     # ... existing fields ...
   
#     # Add this relationship:
#     event_bindings = relationship("EventBinding", back_populates="sprite", cascade="all, delete-orphan")"""