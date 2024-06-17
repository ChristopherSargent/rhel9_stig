![alt text](swclogo.jpg)
# rhel9_stig
This repository contains a script to parse the ansible playbook produced by compliance as code in an effort to modularize it. For additional details, please email at [christopher.sargent@sargentwalker.io](mailto:christopher.sargent@sargentwalker.io).

# Stage rhel9-playbook.yml
* Note that it is added already in this repository but if you need to create a new one here are the manual steps.

1. ssh user@rhel9.server
2. sudo -i 
3. hostnamectl set-hostname hostname
4. echo "export PROMPT_COMMAND='echo -n \[\$(date +%F-%T)\]\ '" >> /etc/bashrc && echo "export HISTTIMEFORMAT='%F-%T '" >> /etc/bashrc && source /etc/bashrc
5. subscription-manager register
6. dnf upgrade -y && reboot
7. ssh user@rhel9.server
8. sudo -i 
9. subscription-manager repos --enable codeready-builder-for-rhel-9-$(arch)-rpms
10. rpm --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-9
11. dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm -y
12. dnf install scap-security-guide yum-utils htop git ansible -y 
13. ll /usr/share/scap-security-guide/ansible
```
total 15600
-rw-r--r--. 1 root root 1246164 May 21 09:42 rhel9-playbook-anssi_bp28_enhanced.yml
-rw-r--r--. 1 root root 1269576 May 21 09:42 rhel9-playbook-anssi_bp28_high.yml
-rw-r--r--. 1 root root  531954 May 21 09:42 rhel9-playbook-anssi_bp28_intermediary.yml
-rw-r--r--. 1 root root  242888 May 21 09:42 rhel9-playbook-anssi_bp28_minimal.yml
-rw-r--r--. 1 root root  723913 May 21 09:42 rhel9-playbook-ccn_advanced.yml
-rw-r--r--. 1 root root  475541 May 21 09:42 rhel9-playbook-ccn_basic.yml
-rw-r--r--. 1 root root  537077 May 21 09:42 rhel9-playbook-ccn_intermediate.yml
-rw-r--r--. 1 root root  617476 May 21 09:42 rhel9-playbook-cis_server_l1.yml
-rw-r--r--. 1 root root  614535 May 21 09:42 rhel9-playbook-cis_workstation_l1.yml
-rw-r--r--. 1 root root 1361930 May 21 09:42 rhel9-playbook-cis_workstation_l2.yml
-rw-r--r--. 1 root root 1366595 May 21 09:42 rhel9-playbook-cis.yml
-rw-r--r--. 1 root root  322060 May 21 09:42 rhel9-playbook-cui.yml
-rw-r--r--. 1 root root  324397 May 21 09:42 rhel9-playbook-e8.yml
-rw-r--r--. 1 root root  879368 May 21 09:42 rhel9-playbook-hipaa.yml
-rw-r--r--. 1 root root  561540 May 21 09:42 rhel9-playbook-ism_o.yml
-rw-r--r--. 1 root root  321576 May 21 09:42 rhel9-playbook-ospp.yml
-rw-r--r--. 1 root root  987480 May 21 09:42 rhel9-playbook-pci-dss.yml
-rw-r--r--. 1 root root 1773126 May 21 09:42 rhel9-playbook-stig_gui.yml
-rw-r--r--. 1 root root 1775569 May 21 09:42 rhel9-playbook-stig.yml
```
14. scp rhel9-playbook-stig.yml to awx or rhel9_stig repo

# Run convert_cas.py
1. ssh user@awx.or.aap
2. sudo -i
3. cd /var/lib/awx
4. mkdir rhel9_stig
5. cd rhel9_stig
6. vim rhel9_stig.yml
```
---
  - name: rhel9_stig
    hosts: all
    gather_facts: yes
    become_user: root
    tasks:
    - name: Include compliance as code role
      include_role:
        name: compliance_as_code

    - name: Load variables from stig_vars.yml
      include_vars:
        file: roles/rhel9_stig/vars/stig_vars.yml

    - name: Include RHEL9 STIG role
      include_role:
        name: rhel9_stig


```
7. python3 convert_cac.py 
* This should parse rhel9-playbook-stig.yml into roles/rhel9_stig/tasks/main.yml and roles/rhel9_stig/vars/stig_vars.yml
8. Configure AAP/AWX as needed.
* Note I had to create awx-ee-legacy execution environment which uses ansible 2.14 for this to run.
9. sed -i -e 's|var_accounts_maximum_age_login_defs: !!str 60|var_accounts_maximum_age_login_defs: !!str 99999|g' /var/lib/awx/projects/rhel9_stig/roles/rhel9_stig/vars/stig_vars.yml
* Note to set this temporarily or you will get locked out
10. vim roles/rhel9_stig/tasks/main.yml
* Add ignore_errors: true to this task
```
      - name: Create USBGuard Policy configuration
        command: usbguard generate-policy
        register: policy
        when: not policy_file.stat.exists or policy_file.stat.size == 0

      - name: Copy the Generated Policy configuration to a persistent file
        copy:
          content: '{{ policy.stdout }}'
          dest: /etc/usbguard/rules.conf
          mode: 384
        when: not policy_file.stat.exists or policy_file.stat.size == 0

      - name: Add comment into /etc/usbguard/rules.conf when system has no USB devices
        lineinfile:
          path: /etc/usbguard/rules.conf
          line: '# No USB devices found'
          state: present
        when: not policy_file.stat.exists or policy_file.stat.size == 0

      - name: Enable service usbguard
        systemd:
          name: usbguard
          enabled: 'yes'
          state: started
          masked: 'no'
      when:
      - ( ansible_virtualization_type not in ["docker", "lxc", "openvz", "podman", "container"]
        and ansible_architecture != "s390x" )
      - '"usbguard" in ansible_facts.packages'
      tags:
      - CCE-88882-6
      - DISA-STIG-RHEL-09-291030
      - NIST-800-53-CM-8(3)(a)
      - NIST-800-53-IA-3
      - configure_strategy
      - low_complexity
      - low_disruption
      - medium_severity
      - no_reboot_needed
      - usbguard_generate_policy
      # Add ignore_errors: true here as there seems to be an issue with this running CAS
      ignore_errors: true
``` 

# Add awx-legacy-ee to SWC AWX
* [awx-legacy-ee](https://drive.google.com/file/d/1GMf7oJScIrijDUYZjFK_YY2heI6-3WFQ/view?usp=drive_link).
1. scp awx-legacy-ee.tar.gz user@awx.or.aap:
2. ssh user@awx.or.aap
3. sudo -i 
4. docker cp  awx-legacy-ee.tar.gz tools_awx_1:/awx_devel
5. docker exec -it -u:0 tools_awx_1 bash
6. mv /awx_devel/awx-legacy-ee.tar.gz /var/lib/awx
7. gunzip -d awx-legacy-ee.tar.gz
8. podman load -i awx-legacy-ee.tar
9. podman image ls
```
REPOSITORY                                                            TAG         IMAGE ID      CREATED      SIZE
quay.io/ansible/awx-ee                                                06162024    8d3970a37561  3 hours ago  1.83 GB
quay.io/ansible/awx-ee                                                latest      799c60ca589b  12 days ago  1.82 GB
registry.redhat.io/ansible-automation-platform-24/ee-supported-rhel8  latest      b1ef3585f1f6  4 weeks ago  1.53 GB
quay.io/ansible/awx-legacy-ee 
```
10. https://awx.or.aap/ > Administration > Execution Environments > Add > 
Name: AWX Legacy EE (Latest)
Image: quay.io/ansible/awx-legacy-ee:latest
Defaults on the rest
> Save
11. Set defualt execution environment to AWX Legacy EE (Latest) due the issue with awx-ee has ansible core 2.15 + and the playbook genereated from oscap xccdf generate fix --profile xccdf_org.ssgproject.content_profile_stig --fix-type ansible /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml > rhel9-playbook-stig.yml uses ini_file module that doesnt work with ansible 2.15 and higher
* Get an error like 
```
TASK [include_role : swc_rhel9_stig] *******************************************
ERROR! couldn't resolve module/action 'ini_file'. This often indicates a misspelling, missing collection, or incorrect module path.
The error appears to be in '/runner/project/roles/swc_rhel9_stig/tasks/main.yml': line 1552, column 5, but may
be elsewhere in the file depending on the exact syntax proble
```
