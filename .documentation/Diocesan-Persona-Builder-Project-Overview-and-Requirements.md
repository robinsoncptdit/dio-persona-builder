# **Diocesan Persona Builder Project Overview and Requirements**

## **1. Project Overview**

The Diocesan Persona Builder is a lightweight Python application that automates the generation of user personas for Catholic diocesan environments (Pastoral Center, Parishes, Schools, Ministries). It leverages a pre-mapped CSV of diocesan roles to O*NET occupation codes and interacts with the O*NET Web Services API to fetch detailed descriptors (skills, tasks, work context, importance scores). The end result is a set of structured, data-driven persona profiles in Markdown format, ready for review and customization.

**Goals:** 

* Streamline persona creation using authoritative occupational data

* Reduce manual effort in persona seeding and maintenance

* Provide flexible, scriptable outputs suitable for integration into documentation or UX tools

## **2. Key Features & Requirements**

### **2.1 Input & Data Sources**

* **Roles CSV**: diocesan_roles_onet.csv containing columns:

  * role_title, setting, onet_code, onet_title, mapping_notes

* **O*NET API Credentials**: Secure storage of client ID/secret or API key

### **2.2 Core Functionality**

1. **CSV Loader**: Read and validate the roles CSV

2. **O*NET Query Module**:

   * Connect to O*NET Web Services using provided credentials

   * For each unique onet_code, fetch:

     * Skills

     * Work Activities (Tasks)

     * Knowledge domains

     * Importance and Level scores

     * Work Styles & Context details

3. **Persona Template Generator**:

   * Merge O*NET descriptors with original role_title and setting

   * Populate a Markdown persona template with sections:

     * **Name & Setting**

     * **Role Summary** (onet_title + mapping_notes)

     * **Key Tasks**

     * **Top Skills & Knowledge** (with importance rank)

     * **Work Context**

     * **Motivations & Work Styles**

4. **Output Module**:

   * Generate one Markdown file per role (filename pattern: persona_<role_slug>.md)
   
⠀
### **2.3 Nonfunctional Requirements**

* **Modularity**: Clear separation between data loading, API access, and template generation (Jinja2 for templating perhaps?)

* **Configuration**: config file for API endpoints, output paths, template settings

* **Error Handling**: Retry logic for API calls, logging of failures, and CSV row validation errors

* **Documentation**: Inline docstrings + a user guide README.md

* **Testing**: Unit tests for CSV parsing, API wrapper, and template rendering

## **3. Implementation Addendum - Upgrades & Enhancements**

*Added: December 6, 2025*

The Diocesan Persona Builder has been successfully implemented with significant enhancements beyond the original requirements. This addendum documents the upgrades completed during development.

### **3.1 Architectural Enhancements**

#### **Agent-Based Architecture**
- **Implementation**: Adopted modern agent-first design patterns using CrewAI and PydanticAI frameworks
- **Benefits**: Improved modularity, better separation of concerns, and enhanced scalability
- **Location**: `src/diocesan_persona_builder/agents/persona_builder_agent.py`

#### **Advanced Configuration Management**
- **Implementation**: Pydantic Settings with environment variable support and validation
- **Features**: 
  - Type-safe configuration with automatic validation
  - .env file support for credentials
  - Hierarchical configuration with defaults
- **Location**: `src/diocesan_persona_builder/core/config.py`

### **3.2 User Experience Improvements**

#### **Rich CLI Interface**
- **Implementation**: Beautiful terminal UI using Click and Rich libraries
- **Features**:
  - Colorized output with progress bars
  - Interactive command structure with helpful descriptions
  - Table-formatted data display
  - Real-time progress tracking for API calls
- **Commands Added**:
  - `validate`: Pre-flight CSV validation with detailed error reporting
  - `load`: Display roles with pagination support
  - `fetch`: Standalone O*NET data fetching with caching
  - `generate`: Complete pipeline execution
  - `info`: System configuration display

#### **Enhanced Error Handling**
- **Implementation**: Comprehensive error handling with user-friendly messages
- **Features**:
  - Retry logic with exponential backoff for API failures
  - Rate limiting to prevent API throttling
  - Detailed error context for debugging
  - Graceful degradation when optional data is unavailable

### **3.3 Data Processing Enhancements**

#### **Intelligent Caching System**
- **Implementation**: Local caching of O*NET API responses
- **Benefits**: 
  - Reduced API calls for repeated runs
  - Faster persona generation
  - Offline capability for cached data
- **Cache Management**: Automatic cache invalidation with `--force` flag

#### **Extended O*NET Data Collection**
- **Original Requirement**: Skills, Tasks, Knowledge, Work Context
- **Enhanced Collection**:
  - **Abilities**: Physical and cognitive abilities required
  - **Work Styles**: Personality traits and characteristics
  - **Technology Skills**: Specific software and tools used
  - **Work Values**: What motivates workers in the role
  - **Interests**: Holland Code (RIASEC) profiles
- **Result**: More comprehensive and nuanced personas

### **3.4 Output Enhancements**

#### **Enriched Persona Templates**
- **Implementation**: Advanced Jinja2 templates with conditional rendering
- **New Sections Added**:
  - **Technology Proficiency**: Categorized by skill level
  - **User Persona Profile**: Demographics, goals, pain points
  - **Digital Literacy Assessment**: Based on technology requirements
  - **Communication Patterns**: Derived from work context
  - **Collaboration Needs**: Team interaction requirements

#### **Technology Filtering System**
- **Implementation**: Optional OpenAI integration for intelligent technology categorization
- **Features**:
  - Filters generic technology skills
  - Groups related technologies
  - Provides relevance scoring
- **Configuration**: Optional via OPENAI_API_KEY environment variable

### **3.5 Development & Testing Enhancements**

#### **Comprehensive Test Suite**
- **Coverage**: Unit tests for all core modules
- **Features**:
  - Pytest with fixtures and mocks
  - Test coverage reporting
  - Integration tests for API interactions
  - Mock O*NET responses for offline testing

#### **Development Tools**
- **Code Quality**: Black, flake8, mypy integration
- **Package Management**: setup.py with development mode support
- **Documentation**: Comprehensive README with examples

### **3.6 Performance Optimizations**

#### **Concurrent Processing**
- **Implementation**: Batch API requests where possible
- **Rate Limiting**: Configurable delays to respect API limits
- **Memory Efficiency**: Streaming processing for large CSV files

### **3.7 Additional Features**

#### **Multiple Output Formats**
- **Templates Directory**: Support for custom persona templates
- **Flexible Naming**: Configurable output file patterns
- **Batch Processing**: Generate all personas with single command

#### **Logging & Monitoring**
- **Implementation**: Configurable logging levels
- **Features**:
  - Detailed API call logging
  - Performance metrics
  - Error tracking with context

### **3.8 Technology Stack Upgrade**

**Original Stack Implied**: Basic Python with requests library

**Implemented Stack**:
- **Core**: Python 3.8+ with type hints
- **CLI**: Click 8.1+ with command groups
- **Configuration**: Pydantic 2.0+ with settings management
- **Templates**: Jinja2 3.1+ with custom filters
- **HTTP**: Requests with Tenacity for retries
- **Data**: Pandas for CSV processing
- **UI**: Rich for terminal formatting
- **AI/Agents**: CrewAI, PydanticAI for agent patterns
- **Testing**: Pytest with coverage reporting

### **3.9 Future-Ready Architecture**

The implementation includes hooks for future enhancements:
- Plugin system for custom data sources
- API versioning support
- Multi-language persona generation
- Export to various formats (JSON, YAML, etc.)
- Integration with persona management systems

This implementation not only meets all original requirements but provides a robust, scalable foundation for future diocesan persona management needs.

