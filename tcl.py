
class TclScript:

    def _tcl(self, s):
        self._tcl_string += s + "\n"

    def __init__(self, project_dir):
        self._tcl_string = ""
        self._tcl("cd " + project_dir)
        self._tcl("open_project ./base.xpr")
        self._tcl("set_msg_config -id {IP_Flow 19-1099} -new_severity {Warning}")

    def create_IP(self, name, register_count):
        if not str(name).replace('_', '').isalnum():
            raise RuntimeError("IP name must be alphanumeric + underscore")

        if register_count < 4:
            register_count = 4

        if register_count > 512:
            raise RuntimeError("IP cannot have more than 512 registers")

        self._tcl('set component_name "%s"' % name)
        self._tcl('set axi_register_count %d' % register_count)
        self._tcl("""set component_core_id [create_peripheral xilinx.com user ${component_name} 1.0 -dir ../../../ip]
add_peripheral_interface S00_AXI -interface_mode slave -axi_type lite ${component_core_id}
set_property VALUE ${axi_register_count} [ipx::get_bus_parameters WIZ_NUM_REG -of_objects [ipx::get_bus_interfaces S00_AXI -of_objects ${component_core_id}]]
generate_peripheral -driver -bfm_example_design -debug_hw_example_design ${component_core_id}
write_peripheral ${component_core_id}
update_ip_catalog -rebuild""")

    def edit_IP(self, name, new_source_path):
        self._tcl('set component_name "%s"' % name)
        self._tcl('ipx::edit_ip_in_project -upgrade true -name ${component_name}_project -directory ./base.tmp/${component_name}_project ../../../ip/${component_name}_1.0/component.xml')
        self._tcl('file copy -force "%s" [get_files "*[get_property top [current_fileset]]*AXI.v"]' % new_source_path)
        self._tcl("""ipx::merge_project_changes files [ipx::current_core]
ipx::update_checksums [ipx::current_core]
ipx::save_core [ipx::current_core]
set_property core_revision [expr [get_property core_revision [ipx::current_core]] + 1] [ipx::current_core]
ipx::update_source_project_archive -component [ipx::current_core]
ipx::create_xgui_files [ipx::current_core]
ipx::update_checksums [ipx::current_core]
ipx::save_core [ipx::current_core]
ipx::move_temp_component_back -component [ipx::current_core]
close_project -delete""")

    def add_IP(self, name):
        self._tcl('set component_name "%s"' % name)
        self._tcl("""update_ip_catalog -rebuild
open_bd_design {./base.srcs/sources_1/bd/base/base.bd}
create_bd_cell -type ip -vlnv xilinx.com:user:${component_name}:1.0 ${component_name}_0
apply_bd_automation -rule xilinx.com:bd_rule:axi4 -config { Clk_master {/ps7_0/FCLK_CLK0 (100 MHz)} Clk_slave {Auto} Clk_xbar {/ps7_0/FCLK_CLK0 (100 MHz)} Master {/ps7_0/M_AXI_GP0} Slave {/${component_name}_0/S00_AXI} intc_ip {/ps7_0_axi_periph} master_apm {0}}  [get_bd_intf_pins ${component_name}_0/S00_AXI]""")

    def delete_IP(self, name):
        self._tcl('set component_name "%s"' % name)
        self._tcl("""open_bd_design {./base.srcs/sources_1/bd/base/base.bd}
delete_bd_objs [get_bd_cells ${component_name}*]
update_ip_catalog -quiet -delete_ip xilinx.com:user:${component_name}:1.0 -repo_path ../../../ip
file delete -force [glob -nocomplain ../../../ip/${component_name}*]""")

    def compile(self):
        self._tcl("""report_ip_status
catch {upgrade_ip [get_ips *]}

reset_run synth_1
reset_run impl_1

launch_runs synth_1
wait_on_run synth_1

set synth_status [ get_property STATUS [get_runs synth_1] ]
if { ${synth_status} eq "synth_design Complete!" } {
    puts "Synthesis complete"
} else {
    puts "Synthesis failed"
    exit 2
}

launch_runs impl_1 -to_step write_bitstream -jobs 16
wait_on_run impl_1


set impl_status [ get_property STATUS [get_runs impl_1] ]
if { ${impl_status} eq "write_bitstream Complete!" } {
    puts "Implementation complete"
} else {
    puts "Implementation failed"
    exit 3
}

file copy -force ./base.runs/impl_1/base_wrapper.bit ../../../overlay.bit
write_bd_tcl -force ../../../overlay.tcl
exit 0""")

    def __str__(self):
        return self._tcl_string
