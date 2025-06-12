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
5. **Single-role Generation**: Allow specifying a single role (by slug or exact title) via a CLI flag (`--role`) to regenerate or update just that persona.
6. <CRITICAL>
   **OpenAI API Prompt Conversion**  
   - Invoke ChatGPT with `conversion-prompt.md`  
   - Transform occupational persona → user persona  
   - Save as `user_persona_<role_slug>.md`  
   - Enforce bullet ≤ 15 words, "—" for blanks  
   </CRITICAL>
   
⠀
### **2.3 Nonfunctional Requirements**

* **Modularity**: Clear separation between data loading, API access, and template generation (Jinja2 for templating perhaps?)

* **Configuration**: config file for API endpoints, output paths, template settings

* **Error Handling**: Retry logic for API calls, logging of failures, and CSV row validation errors

* **Documentation**: Inline docstrings + a user guide README.md

* **Testing**: Unit tests for CSV parsing, API wrapper, and template rendering

* **Logging**: Persistent file logging of CLI runs with timestamped log files; configurable via `--log-file`.

* **CLI Visuals**: Enhanced Rich-based console with per-role and overall progress bars.

