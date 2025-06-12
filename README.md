# Diocesan Persona Builder

A lightweight Python CLI tool that automates the generation of user personas for Catholic diocesan environments using O*NET occupational data.

## Overview

The Diocesan Persona Builder streamlines persona creation by:

1. **Loading diocesan roles** from a CSV file mapped to O*NET occupation codes
2. **Fetching detailed occupational data** from the O*NET Web Services API (skills, tasks, knowledge, work context)
3. **Generating structured persona profiles** in Markdown format using Jinja2 templates

Built with an agent-first architecture using modern Python frameworks including Pydantic for data validation, Click for CLI interface, and comprehensive error handling with retry logic.

## Features

- 🏛️ **Diocesan-specific**: Tailored for Catholic Church environments (Parishes, Schools, Pastoral Centers)
- 🌐 **O*NET Integration**: Authoritative occupational data from the U.S. Department of Labor
- 🤖 **Agent-based Architecture**: Modular design using CrewAI/PydanticAI patterns
- 📊 **Rich CLI Interface**: Beautiful terminal output with progress tracking
- 🔄 **Robust Error Handling**: Retry logic, rate limiting, and comprehensive logging
- 🧪 **Fully Tested**: Comprehensive unit test coverage
- 📝 **Flexible Templates**: Customizable Jinja2 templates for persona output

## Installation

### Prerequisites

- Python 3.8 or higher
- O*NET Web Services API credentials (free registration at [O*NET Interest Profiler](https://services.onetcenter.org/))

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd diocesan-persona-builder
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install package in development mode:**
   ```bash
   pip install -e .
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your O*NET credentials
   ```

   Required environment variables:
   ```env
   ONET_USERNAME=your_onet_username
   ONET_PASSWORD=your_onet_password
   ```

## Quick Start

### 1. Prepare Your CSV File

Create a CSV file with diocesan roles mapped to O*NET codes:

```csv
role_title,setting,onet_code,onet_title,mapping_notes
Parish Secretary,Parish,43-6014.00,Secretaries and Administrative Assistants,Core administrative role
Youth Minister,Parish,21-1021.00,"Child, Family, and School Social Workers",Focus on youth programs
School Principal,School,11-9032.00,"Education Administrators, Kindergarten through Secondary",
```

Required columns:
- `role_title`: Name of the diocesan role
- `setting`: Work environment (Parish, School, Pastoral Center, etc.)
- `onet_code`: O*NET occupation code (format: XX-XXXX.XX)
- `onet_title`: O*NET occupation title
- `mapping_notes`: Optional notes about the mapping

### 2. Validate Your CSV

```bash
diocesan-persona-builder validate data/roles.csv
```

### 3. Generate Personas

```bash
diocesan-persona-builder generate data/roles.csv --output-dir output/personas
```

This will:
- Load all roles from the CSV
- Fetch occupational data from O*NET for each unique code
- Generate markdown persona files in the output directory

## CLI Commands

### `validate <csv_path>`
Validate CSV file structure and display summary.

```bash
diocesan-persona-builder validate data/roles.csv
```

### `load <csv_path>`
Load and display roles from CSV file.

```bash
diocesan-persona-builder load data/roles.csv --limit 10
```

### `fetch <csv_path>`
Fetch O*NET data for all roles in CSV.

```bash
diocesan-persona-builder fetch data/roles.csv --force
```

Options:
- `--force`: Force refresh of cached data

### `generate <csv_path>`
Complete pipeline: load CSV, fetch O*NET data, generate personas.

```bash
diocesan-persona-builder generate data/roles.csv --output-dir output --force
```

Options:
- `--output-dir`: Output directory for persona files (default: `output`)
- `--force`: Force refresh of cached O*NET data

### `info`
Display configuration and system information.

```bash
diocesan-persona-builder info
```

## Generated Persona Format

Each persona includes:

- **Overview**: Role title, setting, O*NET mapping
- **Role Summary**: Occupation description from O*NET
- **Key Tasks**: Primary responsibilities for the role
- **Essential Skills**: Top skills ranked by importance
- **Required Knowledge**: Key knowledge areas with importance scores
- **Work Context**: Interaction patterns, schedule, work environment
- **Work Styles**: Behavioral characteristics and motivations
- **User Persona Profile**: Demographics, goals, pain points, technology needs

Example output snippet:
```markdown
# Persona: Parish Secretary

## Overview
**Role Title:** Parish Secretary  
**Setting:** Parish  
**O*NET Code:** 43-6014.00  
**O*NET Title:** Secretaries and Administrative Assistants  

## Essential Skills
### 1. Reading Comprehension
- **Importance:** 75% (Very Important)

### 2. Active Listening  
- **Importance:** 72% (Very Important)
```

## Configuration

The application uses Pydantic for configuration management with support for:

- **Environment variables** (`.env` file)
- **Configuration validation**
- **Default values**

Key configuration options:

```python
# API Configuration
api_config:
  base_url: "https://services.onetcenter.org/ws"
  timeout: 30
  max_retries: 3
  rate_limit_delay: 0.5

# Output Configuration  
output_config:
  output_dir: "output"
  template_dir: "templates"
  file_pattern: "persona_{role_slug}.md"
```

## Template Customization

Personas are generated using Jinja2 templates. The default template is at `diocesan_persona_builder/templates/persona.md.j2`.

### Available Template Variables

- `role_title`, `setting`, `onet_code`, `onet_title`, `mapping_notes`
- `occupation_description`
- `top_skills`: List of skills with importance scores
- `top_knowledge`: List of knowledge areas with importance scores  
- `key_tasks`: List of primary tasks
- `work_context`: Dictionary of work context categories
- `work_styles`: List of work styles with descriptions
- `generated_at`: Timestamp

### Custom Templates

Create custom templates in the `templates/` directory:

```jinja2
# Custom template example
# {{ role_title }} - {{ setting }}

**O*NET Mapping:** {{ onet_code }} - {{ onet_title }}

## Top 5 Skills
{% for skill in top_skills[:5] %}
- {{ skill.name }} ({{ skill.importance|round }}%)
{% endfor %}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=diocesan_persona_builder

# Run specific test file
pytest diocesan_persona_builder/tests/test_csv_loader.py
```

### Code Quality

```bash
# Format code
black diocesan_persona_builder/

# Lint code
flake8 diocesan_persona_builder/

# Type checking
mypy diocesan_persona_builder/
```

### Project Structure

```
diocesan_persona_builder/
├── agents/                 # Agent-based components
│   └── persona_builder_agent.py
├── core/                   # Core functionality
│   ├── config.py          # Configuration management
│   ├── csv_loader.py      # CSV data loading
│   ├── onet_api.py        # O*NET API client
│   └── template_engine.py # Jinja2 templating
├── templates/              # Jinja2 templates
│   └── persona.md.j2      # Default persona template
├── tests/                  # Unit tests
├── data/                   # Sample data files
├── output/                 # Generated personas
└── cli.py                  # CLI interface
```

## Troubleshooting

### Common Issues

1. **O*NET API Authentication Errors**
   - Verify credentials in `.env` file
   - Check O*NET account status
   - Test with `diocesan-persona-builder info`

2. **CSV Validation Failures**
   - Ensure all required columns are present
   - Check O*NET code format (XX-XXXX.XX)
   - Validate data types

3. **Template Rendering Errors**
   - Check Jinja2 template syntax
   - Verify template file permissions
   - Review template variables

4. **Rate Limiting**
   - Default rate limiting: 0.5 seconds between requests
   - Increase `rate_limit_delay` in configuration if needed

### Logging

Enable debug logging for troubleshooting:

```bash
diocesan-persona-builder --log-level DEBUG generate data/roles.csv
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review O*NET API documentation

---

*Built with modern Python practices and agent-first architecture for reliable, scalable persona generation.*