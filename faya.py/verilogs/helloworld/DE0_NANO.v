module DE0_NANO(
	 // Clock
    input CLOCK_50,
    
    // KEY
    input [1:0] KEY,
    
    // LED
    output [7:0] LED,
    
    // Altri pin della board che potrebbero servire...
    input [3:0] SW,              // Switch
    inout [33:0] GPIO_0         // GPIO_0
    //inout [33:0] GPIO_1          // GPIO_1
);

	assign LED[0] = 1'b1;     // LED sempre acceso

    // Istanza del modulo virtual_jtag_serial
    /*virtual_jtag_serial vjtag_inst (
        .CLOCK_50(CLOCK_50),
        .KEY(KEY),
        .LED(LED)
    );*/

endmodule