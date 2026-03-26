//! Scaffold CLI - Generate web service projects with configurable options

use clap::{Parser, ValueEnum};
use colored::*;
use inquire::Select;
use std::fs;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Supported programming languages
#[derive(Debug, Clone, ValueEnum)]
pub enum Language {
    Go,
    Python,
    Rust,
    C,
}

/// Protocol type for the service
#[derive(Debug, Clone, ValueEnum)]
pub enum Protocol {
    Http,
    Grpc,
    ServiceMesh,
}

/// Database options
#[derive(Debug, Clone, ValueEnum)]
pub enum Database {
    None,
    Postgres,
    PostgresRedis,
}

#[derive(Parser)]
#[command(name = "scaffold")]
#[command(version = "0.1.0")]
#[command(about = "Scaffold web service projects in multiple languages", long_about = None)]
struct Cli {
    /// Project name (required)
    #[arg(short, long)]
    name: Option<String>,

    /// Programming language: go, python, rust, c
    #[arg(short, long, value_enum)]
    language: Option<Language>,

    /// Protocol: http, grpc, mesh
    #[arg(short, long, value_enum)]
    protocol: Option<Protocol>,

    /// Database: none, postgres, postgres-redis
    #[arg(short, long, value_enum)]
    database: Option<Database>,

    /// Output directory (default: current directory)
    #[arg(short, long)]
    output: Option<String>,
}

/// Get interactive input for missing options
fn get_interactive_inputs() -> (String, Language, Protocol, Database) {
    let name = match Cli::parse().name {
        Some(n) => n,
        None => {
            let input = inquire::Text::new("Enter project name:")
                .prompt()
                .expect("Failed to read project name");
            input
        }
    };

    let language = match Cli::parse().language {
        Some(l) => l,
        None => {
            let lang_options = vec!["Go", "Python", "Rust", "C"];
            let selection = Select::new("Select programming language:", lang_options)
                .prompt()
                .expect("Failed to select language");
            match selection {
                "Go" => Language::Go,
                "Python" => Language::Python,
                "Rust" => Language::Rust,
                "C" => Language::C,
                _ => Language::Go,
            }
        }
    };

    let protocol = match Cli::parse().protocol {
        Some(p) => p,
        None => {
            let proto_options = vec!["HTTP only", "gRPC", "Service Mesh"];
            let selection = Select::new("Select protocol:", proto_options)
                .prompt()
                .expect("Failed to select protocol");
            match selection {
                "HTTP only" => Protocol::Http,
                "gRPC" => Protocol::Grpc,
                "Service Mesh" => Protocol::ServiceMesh,
                _ => Protocol::Http,
            }
        }
    };

    let database = match Cli::parse().database {
        Some(d) => d,
        None => {
            let db_options = vec!["None", "PostgreSQL", "PostgreSQL + Redis"];
            let selection = Select::new("Select database:", db_options)
                .prompt()
                .expect("Failed to select database");
            match selection {
                "None" => Database::None,
                "PostgreSQL" => Database::Postgres,
                "PostgreSQL + Redis" => Database::PostgresRedis,
                _ => Database::None,
            }
        }
    };

    (name, language, protocol, database)
}

/// Get template source directory based on language
fn get_template_source(language: &Language) -> PathBuf {
    let base = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    match language {
        Language::Go => base.join("templates").join("go"),
        Language::Python => base.join("templates").join("python"),
        Language::Rust => base.join("templates").join("rust"),
        Language::C => base.join("templates").join("c"),
    }
}

/// Get language display name
fn get_language_name(language: &Language) -> &'static str {
    match language {
        Language::Go => "Go",
        Language::Python => "Python",
        Language::Rust => "Rust",
        Language::C => "C",
    }
}

/// Get language port
fn get_language_port(language: &Language) -> u16 {
    match language {
        Language::Rust => 3001,
        Language::Go => 3002,
        Language::Python => 3003,
        Language::C => 3004,
    }
}

/// Copy template directory to target
fn copy_template(source: &Path, target: &Path) -> std::io::Result<()> {
    if !source.exists() {
        return Err(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("Template source not found: {:?}", source),
        ));
    }

    fs::create_dir_all(target)?;

    for entry in WalkDir::new(source).into_iter().filter_map(|e| e.ok()) {
        let source_path = entry.path();
        let relative_path = source_path.strip_prefix(source).unwrap();
        let target_path = target.join(relative_path);

        if source_path.is_dir() {
            fs::create_dir_all(&target_path)?;
        } else if source_path.is_file() {
            // Copy file
            fs::copy(source_path, &target_path)?;
        }
    }

    Ok(())
}

/// Replace template placeholders in file content
fn replace_placeholders(content: &str, project_name: &str) -> String {
    let mut result = content.to_string();

    // Replace common placeholders
    let placeholders = [
        ("template-name", project_name),
        ("go-template", project_name),
        ("python-template", project_name),
        ("rust-template", project_name),
        ("c-template", project_name),
    ];

    for (placeholder, replacement) in placeholders {
        result = result.replace(placeholder, replacement);
    }

    result
}

/// Apply replacements to all files in directory
fn apply_replacements(project_dir: &Path, project_name: &str) -> std::io::Result<()> {
    for entry in WalkDir::new(project_dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().is_file())
    {
        let path = entry.path();

        // Skip binary files and common exclusions
        if path
            .extension()
            .map(|ext| ext == "lock" || ext == "dockerfile" || ext == "sum")
            .unwrap_or(false)
        {
            continue;
        }

        // Read and replace
        if let Ok(content) = fs::read_to_string(path) {
            let updated = replace_placeholders(&content, project_name);
            if updated != content {
                fs::write(path, updated)?;
            }
        }
    }

    Ok(())
}

/// Generate docker-compose.yml based on options
fn generate_docker_compose(
    project_dir: &Path,
    project_name: &str,
    language: &Language,
    protocol: &Protocol,
    database: &Database,
) -> std::io::Result<()> {
    let port = get_language_port(language);

    let mut services = String::new();

    // Database services
    match database {
        Database::Postgres | Database::PostgresRedis => {
            services.push_str(
                r#"  postgres:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=benchmark
      - POSTGRES_PASSWORD=benchmark123
      - POSTGRES_DB="project_name"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-net

"#,
            );
        }
        Database::None => {}
    }

    if matches!(database, Database::PostgresRedis) {
        services.push_str(
            r#"  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"
    networks:
      - app-net

"#,
        );
    }

    // Service mesh (Consul)
    if matches!(protocol, Protocol::ServiceMesh) {
        services.push_str(
            r#"  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    networks:
      - app-net

"#,
        );
    }

    // Main service
    let mut service_config = format!(
        r#"  {project_name}:
    build: .
    ports:
      - "{port}:{port}"
    restart: unless-stopped
    environment:
      - PORT={port}
"#,
    );

    // Add database env vars and ENABLE_DATABASE flag
    match database {
        Database::Postgres | Database::PostgresRedis => {
            service_config.push_str("      - DATABASE_URL=postgresql://benchmark:benchmark123@postgres:5432/benchmark_db\n");
            service_config.push_str("      - ENABLE_DATABASE=true\n");
        }
        Database::None => {
            service_config.push_str("      - ENABLE_DATABASE=false\n");
        }
    }

    // Add Redis env var
    if matches!(database, Database::PostgresRedis) {
        service_config.push_str("      - REDIS_URL=redis://redis:6379\n");
    }

    // Add gRPC and service mesh flags
    match protocol {
        Protocol::Http => {
            service_config.push_str("      - ENABLE_GRPC=false\n");
            service_config.push_str("      - ENABLE_CONSUL=false\n");
        }
        Protocol::Grpc => {
            service_config.push_str("      - ENABLE_GRPC=true\n");
            service_config.push_str("      - ENABLE_CONSUL=false\n");
        }
        Protocol::ServiceMesh => {
            service_config.push_str("      - ENABLE_GRPC=true\n");
            service_config.push_str("      - ENABLE_CONSUL=true\n");
        }
    }

    // Add service mesh additional env vars (Consul address already handled above)
    if matches!(protocol, Protocol::ServiceMesh) {
        service_config.push_str("      - SERVICE_NAME=project_name\n");
        service_config.push_str("      - CONSUL_ADDR=consul:8500\n");
    }

    // Add depends_on
    match database {
        Database::None => {}
        Database::Postgres => {
            service_config.push_str("    depends_on:\n      - postgres\n");
        }
        Database::PostgresRedis => {
            service_config.push_str("    depends_on:\n      - postgres\n      - redis\n");
        }
    }

    service_config.push_str("    networks:\n      - app-net\n");

    // Replace placeholders in service config
    service_config = replace_placeholders(&service_config, project_name);
    services.push_str(&service_config);

    // Networks and volumes - only include if needed
    let mut networks_volumes = String::new();
    networks_volumes.push_str("networks:\n  app-net:\n    driver: bridge\n\n");

    if matches!(database, Database::Postgres) || matches!(database, Database::PostgresRedis) {
        networks_volumes.push_str("volumes:\n  postgres_data:\n");
    } else {
        networks_volumes.push_str("volumes:\n");
    }

    let compose = format!(
        r#"version: '3.8'

services:
{services}
{networks_volumes}
"#,
        services = services,
        networks_volumes = networks_volumes
    );
    fs::write(project_dir.join("docker-compose.yml"), compose)?;

    Ok(())
}

/// Generate .env.example file
fn generate_env_file(project_dir: &Path, project_name: &str, database: &Database, language: &Language) -> std::io::Result<()> {
    let port = get_language_port(language);

    let mut content = format!(
        r#"# Project Configuration
PROJECT_NAME={}
PORT={}

"#,
        project_name, port
    );

    match database {
        Database::Postgres | Database::PostgresRedis => {
            content.push_str(
                r#"# Database
DATABASE_URL=postgresql://benchmark:benchmark123@postgres:5432/benchmark_db
"#,
            );
        }
        Database::None => {}
    }

    if matches!(database, Database::PostgresRedis) {
        content.push_str(
            r#"# Redis
REDIS_URL=redis://redis:6379
"#,
        );
    }

    fs::write(project_dir.join(".env.example"), content)?;

    Ok(())
}

/// Main scaffolding function
fn scaffold_project(
    name: String,
    language: Language,
    protocol: Protocol,
    database: Database,
    output_dir: Option<String>,
) -> Result<(), Box<dyn std::error::Error>> {
    println!("\n{}", "╔═══════════════════════════════════════════════════════════╗".cyan());
    println!("{}", "║          PROJECT SCAFFOLD CLI".cyan().bold());
    println!("{}", "╚═══════════════════════════════════════════════════════════╝".cyan());

    println!("\n{}", "  📋 Configuration:".yellow());
    println!("      {} Project: {}", "•".green(), name.bold());
    println!("      {} Language: {}", "•".green(), get_language_name(&language));
    println!("      {} Protocol: {}", "•".green(), match &protocol {
        Protocol::Http => "HTTP only",
        Protocol::Grpc => "gRPC",
        Protocol::ServiceMesh => "Service Mesh (HTTP + gRPC + Consul)",
    });
    println!("      {} Database: {}", "•".green(), match &database {
        Database::None => "None",
        Database::Postgres => "PostgreSQL",
        Database::PostgresRedis => "PostgreSQL + Redis",
    });

    // Determine output directory
    let target_dir = match output_dir {
        Some(dir) => PathBuf::from(dir).join(&name),
        None => PathBuf::from(&name),
    };

    println!("\n{}", format!("  📁 Output: {}", target_dir.display()).yellow());

    // Check if directory exists
    if target_dir.exists() {
        return Err(format!("Directory already exists: {:?}", target_dir).into());
    }

    // Get template source
    let template_source = get_template_source(&language);
    println!("\n{}", "  📦 Copying template files...".yellow());

    // Copy template
    copy_template(&template_source, &target_dir)?;

    // Apply replacements
    println!("{}", "  🔄 Replacing placeholders...".yellow());
    apply_replacements(&target_dir, &name)?;

    // Generate docker-compose.yml
    println!("{}", "  📝 Generating docker-compose.yml...".yellow());
    generate_docker_compose(&target_dir, &name, &language, &protocol, &database)?;

    // Generate .env.example
    println!("{}", "  📝 Generating .env.example...".yellow());
    generate_env_file(&target_dir, &name, &database, &language)?;

    println!("\n{}", "  ✅ Project scaffolded successfully!".green().bold());
    println!("\n{}", "  Next steps:".cyan());
    println!("      1. cd {}", name.bold());
    println!("      2. Review .env.example and create .env");
    println!("      3. docker-compose up --build");
    println!();

    Ok(())
}

fn main() {
    // Parse CLI arguments first to check for --help, --version
    let cli = Cli::parse();

    // If --help or --version is used, clap handles it automatically
    // Otherwise, get interactive inputs for missing options
    let (name, language, protocol, database) = if cli.name.is_some()
        || cli.language.is_some()
        || cli.protocol.is_some()
        || cli.database.is_some()
    {
        (
            cli.name.unwrap_or_else(|| {
                inquire::Text::new("Enter project name:")
                    .prompt()
                    .expect("Failed to read project name")
            }),
            cli.language.unwrap_or(Language::Go),
            cli.protocol.unwrap_or(Protocol::Http),
            cli.database.unwrap_or(Database::None),
        )
    } else {
        get_interactive_inputs()
    };

    let output_dir = cli.output;

    // Run scaffolding
    if let Err(e) = scaffold_project(name, language, protocol, database, output_dir) {
        eprintln!("{} Error: {}", "❌".red(), e);
        std::process::exit(1);
    }
}