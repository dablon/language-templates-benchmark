//! Application configuration
//!
//! Loads configuration from environment variables with sensible defaults.

use std::env;

/// Default port if not specified in environment
const DEFAULT_PORT: u16 = 3001;

/// Default log level if not specified
const DEFAULT_LOG_LEVEL: &str = "info";

/// Application configuration loaded from environment
#[derive(Clone, Debug)]
pub struct Config {
    /// Server port
    pub port: u16,
    /// Log level (trace, debug, info, warn, error)
    pub log_level: String,
    /// Application name
    pub app_name: String,
    /// Environment (development, production)
    pub environment: String,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            port: DEFAULT_PORT,
            log_level: DEFAULT_LOG_LEVEL.to_string(),
            app_name: crate::constants::SERVICE_NAME.to_string(),
            environment: "production".to_string(),
        }
    }
}

impl Config {
    /// Load configuration from environment variables
    pub fn from_env() -> Self {
        Self {
            port: env::var("PORT")
                .unwrap_or_default()
                .parse()
                .unwrap_or(DEFAULT_PORT),
            log_level: env::var("LOG_LEVEL")
                .unwrap_or_else(|_| DEFAULT_LOG_LEVEL.to_string()),
            app_name: env::var("APP_NAME")
                .unwrap_or_else(|_| crate::constants::SERVICE_NAME.to_string()),
            environment: env::var("ENVIRONMENT")
                .unwrap_or_else(|_| "production".to_string()),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.port, DEFAULT_PORT);
        assert_eq!(config.log_level, DEFAULT_LOG_LEVEL);
    }
}
