#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/printk.h>
#include <hal/nrf_gpio.h>

#define LED_PIN NRF_GPIO_PIN_MAP(0,27)          // onboard LED (P0.13 on nRF52840 DK)

#define BUTTON_PIN NRF_GPIO_PIN_MAP(0,26) 

int main(void)
{
    nrf_gpio_cfg_output(LED_PIN);
    nrf_gpio_cfg_input(BUTTON_PIN, NRF_GPIO_PIN_PULLUP);

    while (1) {
     
		int pressed = !nrf_gpio_pin_read(BUTTON_PIN); 
        // ! because button pulls LOW when pressed

        if (pressed)
        {
            nrf_gpio_pin_set(LED_PIN);
        }
        else
        {
            nrf_gpio_pin_clear(LED_PIN);
        }

	}
return 0;
}
