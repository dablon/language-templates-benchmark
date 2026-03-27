/**
 * Configuration header
 */

#ifndef CONFIG_H
#define CONFIG_H

#include <stddef.h>

// Service constants
#define SERVICE_NAME "{{PROJECT_NAME}}"
#define VERSION "0.1.0"
#define DEFAULT_PORT 3004

// Get port from environment
int get_port(void);

#endif // CONFIG_H