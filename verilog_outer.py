import math
from component import ComponentSpec


def template(args):
    return """
`timescale 1 ns / 1 ps

module {component_name}_v1_0 #
(
    // Users to add parameters here
    
    // User parameters ends
    // Do not modify the parameters beyond this line
    
    
    // Parameters of Axi Slave Bus Interface S00_AXI
    parameter integer C_S00_AXI_DATA_WIDTH	= 32,
    parameter integer C_S00_AXI_ADDR_WIDTH	= {axi_address_width}
)
(
    // Users to add ports here
    input wire [31:0] video_in,
    input wire video_in_ready,
    input wire [31:0] video_x,
    input wire [31:0] video_y,
    output wire [31:0] video_out,
    // User ports ends
    // Do not modify the ports beyond this line
    
    
    // Ports of Axi Slave Bus Interface S00_AXI
    input wire  s00_axi_aclk,
    input wire  s00_axi_aresetn,
    input wire [C_S00_AXI_ADDR_WIDTH-1 : 0] s00_axi_awaddr,
    input wire [2 : 0] s00_axi_awprot,
    input wire  s00_axi_awvalid,
    output wire  s00_axi_awready,
    input wire [C_S00_AXI_DATA_WIDTH-1 : 0] s00_axi_wdata,
    input wire [(C_S00_AXI_DATA_WIDTH/8)-1 : 0] s00_axi_wstrb,
    input wire  s00_axi_wvalid,
    output wire  s00_axi_wready,
    output wire [1 : 0] s00_axi_bresp,
    output wire  s00_axi_bvalid,
    input wire  s00_axi_bready,
    input wire [C_S00_AXI_ADDR_WIDTH-1 : 0] s00_axi_araddr,
    input wire [2 : 0] s00_axi_arprot,
    input wire  s00_axi_arvalid,
    output wire  s00_axi_arready,
    output wire [C_S00_AXI_DATA_WIDTH-1 : 0] s00_axi_rdata,
    output wire [1 : 0] s00_axi_rresp,
    output wire  s00_axi_rvalid,
    input wire  s00_axi_rready
);
    // Instantiation of Axi Bus Interface S00_AXI
    {component_name}_v1_0_S00_AXI # ( 
    .C_S_AXI_DATA_WIDTH(C_S00_AXI_DATA_WIDTH),
    .C_S_AXI_ADDR_WIDTH(C_S00_AXI_ADDR_WIDTH)
    ) {component_name}_v1_0_S00_AXI_inst (
    .video_in(video_in),
    .video_in_ready(video_in_ready),
    .video_x(video_x),
    .video_y(video_y),
    .video_out(video_out),
    .S_AXI_ACLK(s00_axi_aclk),
    .S_AXI_ARESETN(s00_axi_aresetn),
    .S_AXI_AWADDR(s00_axi_awaddr),
    .S_AXI_AWPROT(s00_axi_awprot),
    .S_AXI_AWVALID(s00_axi_awvalid),
    .S_AXI_AWREADY(s00_axi_awready),
    .S_AXI_WDATA(s00_axi_wdata),
    .S_AXI_WSTRB(s00_axi_wstrb),
    .S_AXI_WVALID(s00_axi_wvalid),
    .S_AXI_WREADY(s00_axi_wready),
    .S_AXI_BRESP(s00_axi_bresp),
    .S_AXI_BVALID(s00_axi_bvalid),
    .S_AXI_BREADY(s00_axi_bready),
    .S_AXI_ARADDR(s00_axi_araddr),
    .S_AXI_ARPROT(s00_axi_arprot),
    .S_AXI_ARVALID(s00_axi_arvalid),
    .S_AXI_ARREADY(s00_axi_arready),
    .S_AXI_RDATA(s00_axi_rdata),
    .S_AXI_RRESP(s00_axi_rresp),
    .S_AXI_RVALID(s00_axi_rvalid),
    .S_AXI_RREADY(s00_axi_rready)
    );

endmodule
""".format(**args)


def template_args(component_spec):
    log_count = math.ceil(math.log2(max(4, component_spec.register_count())))
    axi_address_width = log_count + 2

    return {
        "component_name": component_spec.name,
        "axi_address_width": axi_address_width
    }


def create_wrapper(component_spec):
    return template(template_args(component_spec))


# *****************************************
# Unit tests
# *****************************************

import unittest


class TestVerilogOuter(unittest.TestCase):

    def test_axi_width1(self):
        c = ComponentSpec("name", [
            {"name": f"p{i}", "type": "input"} for i in range(2)
        ])
        a = template_args(c)
        self.assertEqual(a["axi_address_width"], 4)

    def test_axi_width2(self):
        c = ComponentSpec("name", [
            {"name": f"p{i}", "type": "input"} for i in range(5)
        ])
        a = template_args(c)
        self.assertEqual(a["axi_address_width"], 5)

    def test_axi_width3(self):
        c = ComponentSpec("name", [
            {"name": f"p{i}", "type": "input"} for i in range(10)
        ])
        a = template_args(c)
        self.assertEqual(a["axi_address_width"], 6)

    def test_name(self):
        c = ComponentSpec("myname", [])
        a = template_args(c)
        self.assertEqual(a["component_name"], "myname")


if __name__ == '__main__':
    unittest.main()
