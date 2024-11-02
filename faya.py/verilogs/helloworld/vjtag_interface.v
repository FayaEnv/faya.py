module virtual_jtag_serial (
    input wire CLOCK_50,
    input wire [1:0] KEY,
    output wire [7:0] LED
);

    wire tck, tdi, tdo, sdr, udr, cdr;
    reg [7:0] data_reg;
    reg led_state = 0;
    
    // Istanza del componente Virtual JTAG
    sld_virtual_jtag #(
        .sld_auto_instance_index("YES"),
        .sld_instance_index(0),
        .sld_ir_width(1)
    ) virtual_jtag_inst (
        .tdo(tdo),
        .tdi(tdi),
        .tck(tck),
        .ir_out(),
        .ir_in(1'b0),
        .virtual_state_cdr(cdr),
        .virtual_state_sdr(sdr),
        .virtual_state_udr(udr)
    );

    // Registro per il carattere ricevuto
    always @(posedge tck) begin
        if (cdr)
            data_reg <= 8'h00;
        else if (sdr)
            data_reg <= {data_reg[6:0], tdi};
    end

    // Gestione dell'echo e del LED
    always @(posedge tck) begin
        if (udr) begin
            // Se il carattere ricevuto è CR (0x0D) o LF (0x0A)
            if (data_reg == 8'h0D || data_reg == 8'h0A)
                led_state <= ~led_state;
        end
    end

    // Assegnazione dell'output LED
    assign LED[0] = led_state;
    assign LED[7:1] = 7'b0;

    // Loop back del dato ricevuto per l'echo
    assign tdo = (sdr) ? data_reg[7] : 1'b0;

endmodule