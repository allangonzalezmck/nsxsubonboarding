import requests
import json

# Infoblox configuration
INFOBLOX_URL = 'https://infoblox.example.com/wapi/v2.10'
INFOBLOX_USERNAME = 'your_username'
INFOBLOX_PASSWORD = 'your_password'

# NSX-T configuration
NSX_MANAGER = 'https://nsx-manager.example.com'
NSX_USERNAME = 'your_nsx_username'
NSX_PASSWORD = 'your_nsx_password'

# Subnet details
subnets = {
    'dev': '192.168.1.0/24',
    'prod': '192.168.2.0/24',
    'qa': '192.168.3.0/24'
}

# Function to authenticate and get an API token from Infoblox
def get_infoblox_token():
    response = requests.post(
        f'{INFOBLOX_URL}/session',
        auth=(INFOBLOX_USERNAME, INFOBLOX_PASSWORD),
        verify=False
    )
    response.raise_for_status()
    return response.cookies['ibapauth']

# Function to check if a subnet already exists in Infoblox
def infoblox_subnet_exists(token, subnet):
    response = requests.get(
        f'{INFOBLOX_URL}/network',
        params={'network': subnet},
        cookies={'ibapauth': token},
        verify=False
    )
    return response.status_code == 200 and len(response.json()) > 0

# Function to create a subnet in Infoblox
def create_infoblox_subnet(token, subnet, tag):
    data = {
        'network': subnet,
        'extattrs': {
            'Environment': {'value': tag},
            'ManagedBy': {'value': 'Infoblox'}
        }
    }
    response = requests.post(
        f'{INFOBLOX_URL}/network',
        headers={'Content-Type': 'application/json'},
        cookies={'ibapauth': token},
        data=json.dumps(data),
        verify=False
    )
    response.raise_for_status()
    print(f'Infoblox: Subnet {subnet} with tag {tag} created successfully.')

# Function to authenticate and get an API token from NSX-T
def get_nsxt_token():
    response = requests.post(
        f'{NSX_MANAGER}/api/session/create',
        auth=(NSX_USERNAME, NSX_PASSWORD),
        verify=False
    )
    response.raise_for_status()
    return response.json()['token']

# Function to check if a subnet already exists in NSX-T
def nsxt_subnet_exists(token, subnet):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        f'{NSX_MANAGER}/api/v1/logical-switches',
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    logical_switches = response.json()['results']
    for ls in logical_switches:
        if ls['subnets'][0]['network'] == subnet:
            return True
    return False

# Function to create a subnet in NSX-T
def create_nsxt_subnet(token, subnet, tag):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = {
        'display_name': f'{tag}_subnet',
        'subnets': [{'network': subnet}],
        'tags': [{'scope': 'Environment', 'tag': tag}, {'scope': 'ManagedBy', 'tag': 'Infoblox'}]
    }
    response = requests.post(
        f'{NSX_MANAGER}/api/v1/logical-switches',
        headers=headers,
        data=json.dumps(data),
        verify=False
    )
    response.raise_for_status()
    print(f'NSX-T: Subnet {subnet} with tag {tag} created successfully.')

# Main function
def main():
    infoblox_token = get_infoblox_token()
    nsxt_token = get_nsxt_token()

    for tag, subnet in subnets.items():
        # Check and create subnet in Infoblox if not exists
        if infoblox_subnet_exists(infoblox_token, subnet):
            print(f'Infoblox: Subnet {subnet} already exists and is managed by Infoblox.')
        else:
            create_infoblox_subnet(infoblox_token, subnet, tag)

        # Check and create subnet in NSX-T if not exists
        if nsxt_subnet_exists(nsxt_token, subnet):
            print(f'NSX-T: Subnet {subnet} already exists.')
        else:
            create_nsxt_subnet(nsxt_token, subnet, tag)

if __name__ == '__main__':
    main()
