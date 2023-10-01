from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import ssl

class Connect:

    @staticmethod
    def connect_to_esxi():

        # ESXi host details
        esxi_host = input("Enter ESXI Host IP: ") or "[YOUR_IP_ADDR]"
        esxi_username = input("Username: ") or "[YOUR_USERNAME]"
        esxi_password = input("Password: ") or "[YOUR_PASSWORD]"

        try:
            # Disable SSL certificate verification (not recommended for production)
            context = ssl._create_unverified_context()

            service_instance = SmartConnect(
                host=esxi_host,
                user=esxi_username,
                pwd=esxi_password,
                sslContext=context
            )
            return service_instance
        except Exception as e:
            print(f"Failed to connect to ESXi host: {e}")
            return None

    @staticmethod
    def get_esxi_stats(esxi_connection):
        try:
            content = esxi_connection.RetrieveContent()

            # Get the host system
            host_system = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.HostSystem], True
            ).view[0]  # Assumes the first object in the view is the host

            # Get quickStats for CPU and RAM usage
            quick_stats = host_system.summary.quickStats

            # Reference total CPU and RAM capacity
            # This value is hard coded (for the time being) as the API call to get total RAM
            # available was wildly inaccurage. Probably a Layer 8 issue, but this was reliable. 
            total_cpu_mhz = 89000     # CHANGE ME
            total_ram_mb = 60710      # CHANGE ME

            # Calculate the percentage of total resources used
            cpu_usage_percentage = (quick_stats.overallCpuUsage / total_cpu_mhz) * 100
            ram_usage_percentage = (quick_stats.overallMemoryUsage / total_ram_mb) * 100

            # Get the number of VMs and their names
            vm_list = []
            for vm in host_system.vm:
                vm_list.append(vm.name)

            return quick_stats, vm_list, total_cpu_mhz, total_ram_mb, cpu_usage_percentage, ram_usage_percentage
        except Exception as e:
            print(f"Failed to retrieve ESXi stats: {e}")
            return None, None, None, None, None, None

    @staticmethod
    def get_datastore_stats(esxi_connection):
        try:
            content = esxi_connection.RetrieveContent()

            # Get the host system
            host_system = content.viewManager.CreateContainerView(
                content.rootFolder, [vim.HostSystem], True
            ).view[0]  # Assumes the first object in the view is the host

            # Get datastore info
            datastores = host_system.datastore
            datastore_stats = []

            for datastore in datastores:
                summary = datastore.summary
                datastore_name = summary.name
                datastore_capacity = summary.capacity
                datastore_free_space = summary.freeSpace
                datastore_used_space = datastore_capacity - datastore_free_space
                datastore_usage_percentage = (datastore_used_space / datastore_capacity) * 100
                datastore_stats.append((datastore_name, datastore_usage_percentage))

            return datastore_stats
        except Exception as e:
            print(f"Failed to retrieve datastore stats: {e}")
            return None

def main():
    # Connect to ESXi host
    esxi_connection = Connect.connect_to_esxi()

    if not esxi_connection:
        return

    # Get ESXi host stats
    esxi_stats, vm_list, total_cpu_mhz, total_ram_mb, cpu_usage_percentage, ram_usage_percentage = Connect.get_esxi_stats(esxi_connection)
    if not esxi_stats or not vm_list:
        return

    # Display ESXI Host Stats
    print("\n\n   -={     ESXI HOST STATS     }=-\n")
    print(f"CPU Usage: {round(esxi_stats.overallCpuUsage / 1024, 2)} GHz")
    print(f"RAM Usage: {round(esxi_stats.overallMemoryUsage / 1024, 2)} GB")
    print(f"CPU Usage Percentage: {cpu_usage_percentage:.2f}%")
    print(f"RAM Usage Percentage: {ram_usage_percentage:.2f}%")

    # Display VM List
    print("\n\n   -={     VM LIST     }=-\n")
    print(f"Number of VMs: {len(vm_list)}")
    print("VM Names:")
    for vm_name in vm_list:
        print(f"- {vm_name}")

    # Get and Display Datastore Stats
    datastore_stats = Connect.get_datastore_stats(esxi_connection)
    if datastore_stats:
        print("\n\n   -={     DATASTORE STATS     }=-\n")
        for datastore_name, usage_percentage in datastore_stats:
            print(f"Datastore: {datastore_name}")
            print(f"Usage Percentage: {usage_percentage:.2f}%")

    # Disconnect from ESXi host
    Disconnect(esxi_connection)

if __name__ == "__main__":
    main()
