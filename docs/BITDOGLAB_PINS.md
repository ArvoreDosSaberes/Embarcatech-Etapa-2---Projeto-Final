# BitDogLab - Mapeamento de Pinos da RP2040

A **BitDogLab** é uma placa educacional baseada no microcontrolador **RP2040** (Raspberry Pi Pico W), projetada para facilitar o aprendizado de sistemas embarcados e IoT. Este documento descreve a pinagem dos periféricos disponíveis na placa.

---

## Resumo de Pinos Utilizados

| Pino GPIO | Função           | Direção     |
| --------- | ------------------ | ------------- |
| 5         | Botão A           | Input Pull-up |
| 6         | Botão B           | Input Pull-up |
| 7         | Matriz LED WS2812B | Output (Data) |
| 10        | Buzzer Direito     | Output (PWM)  |
| 11        | LED RGB - Verde    | Output (PWM)  |
| 12        | LED RGB - Azul     | Output (PWM)  |
| 13        | LED RGB - Vermelho | Output (PWM)  |
| 14        | I2C1 SDA (OLED)    | I2C           |
| 15        | I2C1 SCL (OLED)    | I2C           |
| 21        | Buzzer Esquerdo    | Output (PWM)  |
| 22        | Joystick - Botão  | Input Pull-up |
| 26        | Joystick - Eixo X  | Input ADC0    |
| 27        | Joystick - Eixo Y  | Input ADC1    |
| 28        | ADC2 (Expansão)   | Input ADC2    |
| -         | Sensor Temp. Interno | ADC4 (interno)|

---

## LED RGB

LED RGB de ânodo comum localizado na placa, controlável via PWM para mistura de cores.

| Cor      | GPIO | Tipo         | Observação                |
| -------- | ---- | ------------ | --------------------------- |
| Vermelho | 13   | Output (PWM) | Ativo em nível baixo (LOW) |
| Verde    | 11   | Output (PWM) | Ativo em nível baixo (LOW) |
| Azul     | 12   | Output (PWM) | Ativo em nível baixo (LOW) |

**Nota:** Por ser ânodo comum, o LED acende quando o pino está em nível LOW. Para controle de intensidade via PWM, valores menores = maior brilho.

```c
// Exemplo de definição
#define LED_R_PIN 13
#define LED_G_PIN 11
#define LED_B_PIN 12
```

---

## Botões

Dois botões tácteis com resistores de pull-up internos já habilitados na placa.

| Botão   | GPIO | Tipo          | Estado Pressionado |
| -------- | ---- | ------------- | ------------------ |
| Botão A | 5    | Input Pull-up | LOW (0)            |
| Botão B | 6    | Input Pull-up | LOW (0)            |

**Nota:** Os botões retornam `0` quando pressionados e `1` quando soltos devido ao pull-up.

```c
// Exemplo de definição
#define BTN_A_PIN 5
#define BTN_B_PIN 6
```

---

## Buzzers

Dois buzzers piezoelétricos para geração de tons e efeitos sonoros. Podem ser controlados via PWM para diferentes frequências.

| Buzzer   | GPIO | Tipo         | Observação   |
| -------- | ---- | ------------ | -------------- |
| Esquerdo | 21   | Output (PWM) | Buzzer passivo |
| Direito  | 10   | Output (PWM) | Buzzer passivo |

**Nota:** Por serem buzzers passivos, é necessário gerar um sinal PWM na frequência desejada para produzir som.

```c
// Exemplo de definição
#define BUZZER_LEFT_PIN  21
#define BUZZER_RIGHT_PIN 10
```

---

## Neopixel - Matrix de LED 5x5

Veja detalhes no arquivo [README da biblioteca Matrix Led BitDogLab](../lib/matrix_led_bitdoglab/README.md).

---

## Joystick Analógico

Joystick analógico de dois eixos com botão central integrado.

| Função | GPIO | Tipo          | Canal ADC | Faixa de Valores       |
| -------- | ---- | ------------- | --------- | ---------------------- |
| Eixo X   | 26   | Input ADC     | ADC0      | 0 - 4095 (12-bit)      |
| Eixo Y   | 27   | Input ADC     | ADC1      | 0 - 4095 (12-bit)      |
| Botão   | 22   | Input Pull-up | -         | LOW quando pressionado |

**Nota:**

- Posição central ≈ 2048 (metade da faixa ADC)
- O botão é ativado pressionando o joystick para baixo

```c
// Exemplo de definição
#define JOYSTICK_X_PIN   26
#define JOYSTICK_Y_PIN   27
#define JOYSTICK_BTN_PIN 22

#define JOYSTICK_X_ADC   0
#define JOYSTICK_Y_ADC   1
```

---

## Display OLED

Display OLED monocromático conectado via barramento I2C.

| Função | GPIO | Tipo      | Barramento |
| -------- | ---- | --------- | ---------- |
| SDA      | 14   | I2C Data  | I2C1       |
| SCL      | 15   | I2C Clock | I2C1       |

**Especificações:**

- **Interface:** I2C (I2C1)
- **Endereço I2C:** 0x3C (padrão para SSD1306)
- **Resolução:** 128x64 pixels (típico)
- **Controlador:** SSD1306
- **Frequência I2C:** Até 400kHz (Fast Mode)

```c
// Exemplo de definição
#define OLED_SDA_PIN 14
#define OLED_SCL_PIN 15
#define OLED_I2C     i2c1
#define OLED_ADDR    0x3C
```

---

## Microfone (se disponível)

Algumas versões da BitDogLab incluem um microfone MEMS para captura de áudio.

| Função | GPIO | Tipo      | Canal ADC |
| -------- | ---- | --------- | --------- |
| Audio    | 28   | Input ADC | ADC2      |

**Nota:** Verificar disponibilidade conforme versão da placa.

---

## Sensor de Temperatura Interno

O RP2040 possui um sensor de temperatura integrado conectado internamente ao canal ADC4. Este sensor mede a temperatura do próprio chip, útil para monitoramento térmico do sistema.

| Função      | GPIO | Tipo         | Canal ADC | Faixa Típica    |
| ----------- | ---- | ------------ | --------- | --------------- |
| Temperatura | -    | Interno      | ADC4      | -20°C a +85°C   |

**Especificações:**

- **Canal ADC:** 4 (interno, sem pino GPIO associado)
- **Tensão de referência:** 0.706V a 27°C
- **Coeficiente:** -1.721 mV/°C
- **Precisão:** ±2°C (típico, sem calibração)

**Fórmula de Conversão:**

```
Temperatura (°C) = 27 - (V_adc - 0.706) / 0.001721
```

Onde `V_adc = (raw_adc * 3.3) / 4096`

```c
// Exemplo de definição e leitura
#define TEMP_ADC_CHANNEL 4

// Habilitar sensor de temperatura
adc_set_temp_sensor_enabled(true);

// Leitura da temperatura
adc_select_input(TEMP_ADC_CHANNEL);
uint16_t raw = adc_read();
float voltage = raw * 3.3f / 4096.0f;
float temperature = 27.0f - (voltage - 0.706f) / 0.001721f;
```

**Notas:**

- O sensor mede a temperatura do die (chip), não a temperatura ambiente
- Útil para detectar superaquecimento ou throttling térmico
- Para maior precisão, recomenda-se calibração com temperatura conhecida
- A leitura pode variar ~5-10°C acima da temperatura ambiente em operação normal

---

## Conector de Expansão (14 Pinos)

Conector superior de 14 pinos para expansão e conexão de módulos externos.

### Layout do Conector (Vista Superior)

| Pino  | 1   | 2  | 3  | 4   | 5  | 6   | 7   |
| ----- | --- | -- | -- | --- | -- | --- | --- |
| Row 1 | GND | 16 | 17 | GND | 28 | 3V3 | GND |
| Row 2 | 18  | 19 | 20 | 4   | 9  | 9   | 5V  |

### Detalhamento dos Pinos de Expansão

| GPIO | Funções Alternativas       | Observação           |
| ---- | ---------------------------- | ---------------------- |
| 4    | SPI0 RX, I2C0 SDA, UART1 TX  | GPIO de uso geral      |
| 9    | SPI1 CSn, I2C0 SCL, UART1 RX | Aparece 2x no conector |
| 16   | SPI0 RX, I2C0 SDA, UART0 TX  | GPIO de uso geral      |
| 17   | SPI0 CSn, I2C0 SCL, UART0 RX | GPIO de uso geral      |
| 18   | SPI0 SCK, I2C1 SDA           | GPIO de uso geral      |
| 19   | SPI0 TX, I2C1 SCL            | GPIO de uso geral      |
| 20   | SPI0 RX, I2C0 SDA, UART1 TX  | GPIO de uso geral      |
| 28   | ADC2                         | Entrada analógica     |

### Alimentação Disponível

| Pino | Tensão | Corrente Máxima         |
| ---- | ------- | ------------------------ |
| 3V3  | 3.3V    | Limitada pelo regulador  |
| 5V   | 5V      | Via USB ou fonte externa |
| GND  | 0V      | Referência comum        |

---

## Diagrama de Blocos

```
                    ┌─────────────────────────────────────┐
                    │           BitDogLab                 │
                    │         (RP2040 / Pico W)           │
                    ├─────────────────────────────────────┤
                    │                                     │
    ┌───────────┐   │  ┌─────────┐    ┌──────────────┐   │
    │ Botão A   │───┼──│ GPIO 5  │    │  LED RGB     │   │
    │ Botão B   │───┼──│ GPIO 6  │    │  R:13 G:11   │   │
    └───────────┘   │  └─────────┘    │  B:12        │   │
                    │                  └──────────────┘   │
    ┌───────────┐   │  ┌─────────┐    ┌──────────────┐   │
    │ Joystick  │───┼──│ GPIO 26 │    │  Buzzers     │   │
    │ X/Y/Btn   │───┼──│ GPIO 27 │    │  L:21 R:10   │   │
    └───────────┘───┼──│ GPIO 22 │    └──────────────┘   │
                    │  └─────────┘                        │
    ┌───────────┐   │  ┌─────────┐    ┌──────────────┐   │
    │ OLED      │───┼──│ GPIO 14 │────│  I2C1        │   │
    │ SSD1306   │───┼──│ GPIO 15 │────│  SDA/SCL     │   │
    └───────────┘   │  └─────────┘    └──────────────┘   │
                    │                                     │
    ┌───────────┐   │  ┌─────────┐    ┌──────────────┐   │
    │ WS2812B   │───┼──│ GPIO 7  │    │  Matriz LED  │   │
    │ Matrix    │   │  └─────────┘    │  5x5 RGB     │   │
    └───────────┘   │                  └──────────────┘   │
                    │                                     │
                    │  ┌─────────────────────────────┐   │
                    │  │   Conector de Expansão      │   │
                    │  │   GPIO: 4,9,16,17,18,19,20  │   │
                    │  │   ADC: 28                   │   │
                    │  │   Power: 3V3, 5V, GND       │   │
                    │  └─────────────────────────────┘   │
                    └─────────────────────────────────────┘
```

---

## Definições Completas para C/C++

```c
#ifndef BITDOGLAB_PINS_H
#define BITDOGLAB_PINS_H

// ===== LED RGB (Ânodo Comum - Ativo LOW) =====
#define LED_R_PIN           13
#define LED_G_PIN           11
#define LED_B_PIN           12

// ===== Botões (Pull-up - Ativo LOW) =====
#define BTN_A_PIN           5
#define BTN_B_PIN           6

// ===== Buzzers (PWM) =====
#define BUZZER_LEFT_PIN     21
#define BUZZER_RIGHT_PIN    10

// ===== Matriz LED WS2812B =====
#define WS2812_PIN          7
#define WS2812_NUM_LEDS     25

// ===== Joystick =====
#define JOYSTICK_X_PIN      26
#define JOYSTICK_Y_PIN      27
#define JOYSTICK_BTN_PIN    22
#define JOYSTICK_X_ADC      0
#define JOYSTICK_Y_ADC      1

// ===== Display OLED (I2C1) =====
#define OLED_SDA_PIN        14
#define OLED_SCL_PIN        15
#define OLED_I2C_INST       i2c1
#define OLED_I2C_ADDR       0x3C

// ===== Sensor de Temperatura Interno =====
#define TEMP_ADC_CHANNEL    4

// ===== Expansão =====
#define EXP_GPIO_4          4
#define EXP_GPIO_9          9
#define EXP_GPIO_16         16
#define EXP_GPIO_17         17
#define EXP_GPIO_18         18
#define EXP_GPIO_19         19
#define EXP_GPIO_20         20
#define EXP_ADC_PIN         28
#define EXP_ADC_CHANNEL     2

#endif // BITDOGLAB_PINS_H
```

---

## Painel Traseiro (8 Pinos)

Conector traseiro da placa BitDogLab que disponibiliza GPIOs adicionais não utilizados pelos periféricos onboard. Este conector é ideal para conexão de sensores externos, atuadores e módulos de comunicação.

### Layout do Conector Traseiro (Vista Traseira)

| Pino | 1   | 2  | 3  | 4   | 5   | 6   | 7   | 8   |
| ---- | --- | -- | -- | --- | --- | --- | --- | --- |
| GPIO | 0   | 1  | 2  | 3   | GND | 8   | 3V3 | 5V  |

### Detalhamento dos Pinos do Painel Traseiro

| GPIO | Funções Alternativas           | Barramento   | Observação               |
| ---- | ------------------------------ | ------------ | ------------------------ |
| 0    | I2C0 SDA, SPI0 RX, UART0 TX    | I2C0         | Dados I2C secundário     |
| 1    | I2C0 SCL, SPI0 CSn, UART0 RX   | I2C0         | Clock I2C secundário     |
| 2    | SPI0 SCK, I2C1 SDA             | SPI0         | GPIO de uso geral / PWM  |
| 3    | SPI0 TX, I2C1 SCL              | SPI0         | GPIO de uso geral / PWM  |
| 8    | SPI1 RX, I2C0 SDA, UART1 TX    | SPI1/I2C0    | GPIO de uso geral        |

### Casos de Uso Comuns

| Aplicação              | GPIOs Utilizados | Protocolo      |
| ---------------------- | ---------------- | -------------- |
| Sensor I2C externo     | 0, 1             | I2C0           |
| Sensor de cor TCS34725 | 0, 1             | I2C0           |
| Servo motor            | 2 ou 3           | PWM            |
| Comunicação SPI        | 2, 3, 8          | SPI0/SPI1      |
| Entrada digital        | 2, 3, 8          | GPIO           |

### Alimentação Disponível no Painel Traseiro

| Pino | Tensão  | Corrente Máxima          |
| ---- | ------- | ------------------------ |
| 3V3  | 3.3V    | Limitada pelo regulador  |
| 5V   | 5V      | Via USB ou fonte externa |
| GND  | 0V      | Referência comum         |

**Notas:**

- O barramento **I2C0** (GPIO 0 e 1) é independente do **I2C1** (GPIO 14 e 15) usado pelo OLED
- Os GPIOs 2 e 3 suportam PWM, ideais para controle de servos
- O GPIO 8 pode ser usado como entrada/saída digital genérica
- Ao utilizar I2C0, verificar compatibilidade de endereços com outros dispositivos

```c
// Exemplo de definição para Painel Traseiro
#define BACK_I2C0_SDA_PIN   0
#define BACK_I2C0_SCL_PIN   1
#define BACK_GPIO_2         2   // PWM compatível
#define BACK_GPIO_3         3   // PWM compatível
#define BACK_GPIO_8         8

#define BACK_I2C_INST       i2c0
```

### Diagrama do Painel Traseiro

```
        ┌─────────────────────────────────────┐
        │       PAINEL TRASEIRO BitDogLab     │
        │   ┌───┬───┬───┬───┬───┬───┬───┬───┐ │
        │   │ 0 │ 1 │ 2 │ 3 │GND│ 8 │3V3│ 5V│ │
        │   └───┴───┴───┴───┴───┴───┴───┴───┘ │
        │     │   │   │   │   │   │   │   │   │
        │   SDA SCL PWM PWM GND GPIO 3V3 5V   │
        │   I2C0    │   │       │             │
        │           └───┘       │             │
        │          SPI0 SCK/TX  │             │
        │                    SPI1 RX          │
        └─────────────────────────────────────┘
```

---

## Definições Completas Atualizadas para C/C++

```c
#ifndef BITDOGLAB_PINS_H
#define BITDOGLAB_PINS_H

// ===== LED RGB (Ânodo Comum - Ativo LOW) =====
#define LED_R_PIN           13
#define LED_G_PIN           11
#define LED_B_PIN           12

// ===== Botões (Pull-up - Ativo LOW) =====
#define BTN_A_PIN           5
#define BTN_B_PIN           6

// ===== Buzzers (PWM) =====
#define BUZZER_LEFT_PIN     21
#define BUZZER_RIGHT_PIN    10

// ===== Matriz LED WS2812B =====
#define WS2812_PIN          7
#define WS2812_NUM_LEDS     25

// ===== Joystick =====
#define JOYSTICK_X_PIN      26
#define JOYSTICK_Y_PIN      27
#define JOYSTICK_BTN_PIN    22
#define JOYSTICK_X_ADC      0
#define JOYSTICK_Y_ADC      1

// ===== Display OLED (I2C1) =====
#define OLED_SDA_PIN        14
#define OLED_SCL_PIN        15
#define OLED_I2C_INST       i2c1
#define OLED_I2C_ADDR       0x3C

// ===== Sensor de Temperatura Interno =====
#define TEMP_ADC_CHANNEL    4

// ===== Conector de Expansão Frontal (14 pinos) =====
#define EXP_GPIO_4          4
#define EXP_GPIO_9          9
#define EXP_GPIO_16         16
#define EXP_GPIO_17         17
#define EXP_GPIO_18         18
#define EXP_GPIO_19         19
#define EXP_GPIO_20         20
#define EXP_ADC_PIN         28
#define EXP_ADC_CHANNEL     2

// ===== Painel Traseiro (8 pinos) =====
#define BACK_I2C0_SDA_PIN   0
#define BACK_I2C0_SCL_PIN   1
#define BACK_GPIO_2         2   // PWM compatível (servo)
#define BACK_GPIO_3         3   // PWM compatível (servo)
#define BACK_GPIO_8         8
#define BACK_I2C_INST       i2c0

#endif // BITDOGLAB_PINS_H
```

---

## Referências

- [Datasheet RP2040](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- [Raspberry Pi Pico SDK](https://github.com/raspberrypi/pico-sdk)
- [Documentação BitDogLab](https://github.com/BitDogLab) *(verificar disponibilidade)*
- [BitDogLab V7 GitLab](https://gitlab.unicamp.br/fabiano/bitdoglab-v7)
