# THIS REPO IS NO LONGER MAINTAINED
Replaced by the ServiceNow Inventory Plugin available an [Ansible Galaxy](https://galaxy.ansible.com/servicenow/servicenow)

# ServiceNow Ansible Inventory
Generates dynamic inventory for Ansible using the ServiceNow CMDB.

# Requirements
- [Ansible](http://docs.ansible.com/intro_getting_started.html)
- Python [requests](http://docs.python-requests.org/en/master/)

# Installation

1. [Install Ansible](http://docs.ansible.com/ansible/intro_installation.html)
2. [Install requests](http://docs.python-requests.org/en/master/user/install/)

Copy the inventory script _now.py_ to the Ansible inventory location, or specify the script with _-i /path/to/now.py_. See the Ansible documentation on [Dynamic Inventory](http://docs.ansible.com/ansible/intro_dynamic_inventory.html#using-inventory-directories-and-multiple-inventory-sources) for usage.

# Usage

The ServiceNow inventory script queries hosts from the `cmdb_ci_server` table. By default, host targets are determined by inspecting the table columns `ip_address`, `fqdn`, and `host_name` in order of priority.  As a result, IP addresses will be prefered over hostnames when both are defined in the server record.

Ansible groups always include the display value of the table column `sys_class_name`. Ansible does not support most non-word characters in group names, so the inventory script will convert group names to lowercase and non-word characters to underscore. Some examples group names include the following:

* linux_server
* esx_server
* windows_server

Additional groups can be configured using the **`SN_GROUPS`** environment variable. See usage and syntax in the **Environment** section.

You can get a list of exposed groups by inspecting the JSON content of the inventory script. The following shell command leverages the [jq](https://stedolan.github.io/jq/) utility to extract all group names.

    $ ./now.py  | jq 'del(.\_meta) | keys[]'

The inventory script makes use of the top level element `_meta`, introduced in Ansible version 1.3 to increase performance with large number of hosts and all hostvars are prefixed with **`sn_`**. By default, the following hostvars are defined for each target host:

* `sn_name`
* `sn_fqdn`
* `sn_ip_address`
* `sn_host_name`
* `sn_sys_class_name`

Additional hostvars can be added by using the environment variable **`SN_FIELDS`**.  See usage and syntax in the **Environment** section.

The ServiceNow inventory script leverages cookies to improve performance and prevent multiple sessions being created from repetitive execution. Cookies are stored in **`${HOME}/.sn_api_session`** using the LWP format.

# Environment

The ServiceNow inventory script is configured through the now.ini config file or by using environment variables.  **`instance=`**, **`username=`** and **`password=`** must be set in the config file or **`SN_INSTANCE`**, **`SN_USERNAME`**, and **`SN_PASSWORD`** environment variables must be set for the script to successfully query the ServiceNow instance CMDB. Environment variables will take precedence over config file if both are set.

This script will attempt to read configuration from a config file with the same base filename .ini if present, or `now.ini` if not.  It is possible to create symlinks to the inventory script to support multiple configurations.

**`NOW_INI`** (optional)

The path to an INI file may also be specified via this environment variable, in which case the filename matching rules above will not apply.

**`SN_INSTANCE`** (required)

The ServiceNow instance URI. The URI should be the fully-qualified domain name, e.g. 'your-instance.servicenow.com'.

    export SN_INSTANCE=your-instance.servicenow.com


**`SN_USERNAME`** (required)

The ServiceNow instance user name. The user acount should have enough rights to read the `cmdb_ci_server` table (default), or the table specified by `SN_TABLE`.

    export SN_USERNAME=user.name


**`SN_PASSWORD`** (required)

The ServiceNow instance user password.

    export SN_PASSWORD=user.password


**`SN_TABLE`** (optional)

The ServiceNow table to query (e.g. cmdb_ci_server, cmdb_ci_netgear, cmdb_ci_win_server, etc.).  This setting will default to `cmdb_ci_server` if not defined.

    export SN_TABLE=cmdb_ci_server


**`SN_FIELDS`** (optional)

Comma seperated string providing additional table columns to add as host vars to each inventory host.

    export SN_FIELDS='company,os,os_version'

Note: empty fields will be ignored and field values must be the column name, not column labels.


**`SN_GROUPS`** (optional)

Comma seperated string providing additional table columns to use as groups. Groups can overlap with `SN_FIELDS`.

    export SN_GROUPS='manufacturer,company,os'

**`SN_SEL_ORDER`** (optional)

Comma seperated string providing ability to define selection preference order. This setting will default to 'host_name,fqdn,ip_address' if not defined.

    export SN_SEL_ORDER='host_name,fqdn,ip_address'

**`SN_CACHE_DIR`** (optional)

Path to directory which will be used to store inventory cache (will be created if path does not exist, path is relative to script if not explicit). If not defined caching will be disabled.

    export SN_CACHE_DIR='.cache/ansible'

**`SN_CACHE_MAX_AGE`** (optional)

Maximum age in seconds of the cache before it will be refreshed with data from the ServiceNow instance CMDB. If not defined will default to 0 (always stale).

    export SN_CACHE_MAX_AGE=3600


**`SN_FILTER_RESULTS`** (optional)

Filter results with [**sysparm_query encoded query string syntax**](https://docs.servicenow.com/bundle/newyork-platform-user-interface/page/use/using-lists/task/t_GenEncodQueryStringFilter.html#t_GenEncodQueryStringFilter).  Complete list of [**operators available for filters and queries**](https://docs.servicenow.com/bundle/newyork-platform-user-interface/page/use/common-ui-elements/reference/r_OpAvailableFiltersQueries.html).  URL encoding [**percent signs**](https://github.com/ServiceNowITOM/ansible-sn-inventory/pull/23#issuecomment-534152050) in the filter string need to be doubled in the now.ini config file.

    export SN_FILTER_RESULTS=operational_status=1^fqdnISNOTEMPTY


**`SN_PROXY`** (optional)

Proxy server to use for requests to ServiceNow. This setting may also be defined with the SN_PROXY environment variable. If not defined no proxy will be used.

    export SN_PROXY='http://myproxy.mydomain.com:8080'



# Example

Once you confirm the dynamic inventory script is working as expected, you can tell Ansible to use the `now.py` script as an inventory file, as illustrated below:

    ansible -i now.py all -m ping

You can narrow the selection using groups created from table columns in the CMDB (default or specified by `SN_GROUPS`) as illustrated below:

    ansible -i now.py linux_server -m ping

If you want to verify the inventory without running the playbook use the `--list-hosts` flag.
