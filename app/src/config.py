class BaseConfig:
    """Base configuration shared across all environments."""

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(BaseConfig):
    """Production configuration."""

    DEBUG = False
