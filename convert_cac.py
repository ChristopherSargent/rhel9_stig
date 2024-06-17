import os

# Create directory structure
os.makedirs('roles/rhel9_stig/tasks', exist_ok=True)
os.makedirs('roles/rhel9_stig/vars', exist_ok=True)

# Define the paths for the new files
tasks_path = 'roles/rhel9_stig/tasks/main.yml'
vars_path = 'roles/rhel9_stig/vars/stig_vars.yml'

# Read the original playbook content
with open('/var/lib/awx/projects/rhel9_stig/rhel9-playbook-stig.yml', 'r') as file:
    playbook_lines = file.readlines()

# Initialize variable content and main content
vars_content = "---\n"
main_content = "---\n"

# Flags to track sections
vars_start = False
tasks_start = False

# Process each line in the playbook
for line in playbook_lines:
    if 'vars:' in line:
        vars_start = True
        tasks_start = False
        continue
    elif 'tasks:' in line:
        vars_start = False
        tasks_start = True
        continue
    
    # Extract and format variables
    if vars_start:
        if line.startswith('  '):  # Only include lines that are indented
            vars_content += line  # Keep the original indentation
    
    # Extract and format tasks
    elif tasks_start:
        if line.startswith('  '):  # Only include lines that are indented
            if line.strip().startswith('- name:'):
                main_content += "\n"  # Add a blank line before each new task
            main_content += line  # Keep the original indentation

# Write the extracted variables to stig_vars.yml
with open(vars_path, 'w') as vars_file:
    vars_file.write(vars_content)

# Write the main playbook content to main.yml
with open(tasks_path, 'w') as tasks_file:
    tasks_file.write(main_content)

