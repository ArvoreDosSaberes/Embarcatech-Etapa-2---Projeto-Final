# Análise RTOS (WCET / Stack / Heap)
Gerado em: `2025-12-25T14:00:03.760732-03:00`
## Parâmetros
- **board**: `None`
- **mcuCode**: `rp2040`
- **projectDir**: `firmware`
- **elf**: `firmware/build/rack_inteligente.elf`

## Heap
- **heap_free**
  - count: `0`
  - min: `None`
  - max: `None`
  - mean: `0.0`
- **heap_min**
  - count: `0`
  - min: `None`
  - max: `None`
  - mean: `0.0`

## Tasks

## Escalonamento / CPU (janela)
Sem dados suficientes de TraceKV para estimar CPU por janela.

### Segmentos de escalonamento (resumo)
| Task | Segments | TotalRunTime(s) | MeanSegment(s) | MaxSegment(s) |
|---|---:|---:|---:|---:|

## ELF/MAP (resumo)
- `map_path`: `firmware/build/rack_inteligente.elf.map`
- `section_bss_bytes`: `218964`
- `section_data_bytes`: `72`
- `section_text_bytes`: `4`

## ELF (maiores símbolos por tamanho)
| Símbolo | Bytes |
|---|---:|
| `w43439A0_7_95_49_00_combined` | `225240` |
| `ucHeap` | `104504` |
| `memp_memory_PBUF_POOL_base` | `49027` |
| `ram_heap` | `24019` |
| `gLines` | `8960` |
| `gLines` | `8960` |
| `vApplicationGetTimerTaskMemory::uxTimerTaskStack` | `4096` |
| `memp_memory_TCP_PCB_base` | `3283` |
| `tcp_receive` | `2504` |
| `cyw43_state` | `2464` |
| `core1_stack` | `2048` |
| `_vsnprintf` | `1700` |
| `tcp_input` | `1632` |
| `main` | `1620` |
| `_malloc_r` | `1484` |
| `tcp_process` | `1376` |
| `cyw43_spi_transfer` | `1324` |
| `tcp_slowtmr` | `1100` |
| `dns_table` | `1088` |
| `_etoa` | `1058` |
| `__malloc_av_` | `1032` |
| `vApplicationGetIdleTaskMemory::uxIdleTaskStack` | `1024` |
| `statsBuffer.0` | `1024` |
| `ssd_buffer` | `1024` |
| `hw_endpoints` | `1024` |
| `memp_memory_TCP_SEG_base` | `963` |
| `mqtt_client_connect` | `916` |
| `process_control_request` | `900` |
| `cyw43_ll_bus_init` | `880` |
| `tcp_write` | `852` |

## Complexidade Ciclomática (McCabe) - análise offline
A complexidade é calculada a partir do assembly (contagem de branches condicionais por função).

- Clock do MCU: `125 MHz`
- Funções analisadas: `1290`
- Tasks identificadas: `69`
- Profundidade máxima do callgraph: `38`
- McCabe médio: `4.51`
- McCabe máximo: `108`

| Função | McCabe | Decisões | Instruções | Ciclos Est. | WCET Est. (μs) | Task |
|---|---:|---:|---:|---:|---:|:---:|
| `tcp_receive` | `108` | `107` | `1121` | `2292` | `18.34` |  |
| `tcp_input` | `72` | `71` | `684` | `1441` | `11.53` |  |
| `tcp_process` | `67` | `66` | `610` | `1298` | `10.38` |  |
| `_vsnprintf` | `65` | `64` | `829` | `1550` | `12.40` |  |
| `_malloc_r` | `62` | `61` | `713` | `1311` | `10.49` |  |
| `tcp_slowtmr` | `62` | `61` | `483` | `1027` | `8.22` |  |
| `dhcp_parse_reply` | `42` | `41` | `349` | `708` | `5.66` |  |
| `tcp_write` | `40` | `39` | `381` | `738` | `5.90` |  |
| `tcp_output` | `40` | `39` | `361` | `729` | `5.83` |  |
| `process_control_request` | `39` | `38` | `399` | `874` | `6.99` |  |
| `_ftoa` | `37` | `36` | `369` | `779` | `6.23` |  |
| `mqtt_message_received` | `37` | `36` | `298` | `618` | `4.94` |  |
| `ip4_input` | `31` | `30` | `301` | `618` | `4.94` |  |
| `_ntoa_format` | `31` | `30` | `134` | `265` | `2.12` |  |
| `mqtt_client_connect` | `29` | `28` | `385` | `814` | `6.51` |  |
| `alarm_pool_irq_handler` | `29` | `28` | `347` | `664` | `5.31` |  |
| `ip_reass_chain_frag_into_datagram_and_validate` | `29` | `28` | `302` | `574` | `4.59` |  |
| `ip4_reass` | `28` | `27` | `289` | `594` | `4.75` |  |
| `udp_input` | `27` | `26` | `232` | `472` | `3.78` |  |
| `dns_recv` | `26` | `25` | `243` | `522` | `4.18` |  |
| `etharp_find_entry` | `26` | `25` | `200` | `383` | `3.06` |  |
| `cyw43_cb_process_async_event` | `26` | `25` | `195` | `423` | `3.38` |  |
| `ip4addr_aton` | `26` | `25` | `164` | `333` | `2.66` |  |
| `_etoa` | `25` | `24` | `438` | `918` | `7.34` |  |
| `handle_name_menu_keys` | `25` | `24` | `222` | `483` | `3.86` |  |
| `i2c_write_blocking_internal` | `25` | `24` | `172` | `335` | `2.68` |  |
| `handle_password_menu_keys` | `24` | `23` | `203` | `442` | `3.54` |  |
| `etharp_query` | `24` | `23` | `202` | `407` | `3.26` |  |
| `pvPortMalloc` | `24` | `23` | `162` | `350` | `2.80` |  |
| `xQueueGenericSend` | `24` | `23` | `152` | `372` | `2.98` |  |
| `pbuf_copy_partial_pbuf` | `22` | `21` | `135` | `277` | `2.22` |  |
| `dhcp_recv` | `22` | `21` | `107` | `230` | `1.84` |  |
| `cyw43_spi_transfer` | `21` | `20` | `597` | `1133` | `9.06` |  |
| `cyw43_ll_bus_init` | `21` | `20` | `328` | `774` | `6.19` |  |
| `_free_r` | `21` | `20` | `235` | `430` | `3.44` |  |
| `best_effort_wfe_or_timeout` | `21` | `20` | `133` | `280` | `2.24` |  |
| `dcd_rp2040_irq` | `20` | `19` | `227` | `459` | `3.67` |  |
| `cdcd_control_xfer_cb` | `20` | `19` | `144` | `308` | `2.46` |  |
| `cdcd_xfer_cb` | `20` | `19` | `141` | `299` | `2.39` |  |
| `cyw43_ll_wifi_join` | `19` | `18` | `334` | `667` | `5.34` |  |
| `sdpcm_process_rx_packet` | `19` | `18` | `164` | `329` | `2.63` |  |
| `xQueueSemaphoreTake` | `19` | `18` | `150` | `377` | `3.02` |  |
| `xQueueGenericSendFromISR` | `19` | `18` | `130` | `282` | `2.26` |  |
| `tcp_close_shutdown` | `19` | `18` | `129` | `297` | `2.38` |  |
| `cyw43_ll_wifi_ap_init` | `18` | `17` | `289` | `589` | `4.71` |  |
| `icmp_input` | `18` | `17` | `224` | `459` | `3.67` |  |
| `dns_enqueue` | `18` | `17` | `182` | `347` | `2.78` |  |
| `cyw43_ll_sdpcm_poll_device` | `18` | `17` | `146` | `317` | `2.54` |  |
| `mem_malloc` | `18` | `17` | `125` | `264` | `2.11` |  |
| `tcp_enqueue_flags` | `17` | `16` | `131` | `276` | `2.21` |  |

### Tasks Identificadas
- **buzzerPwmTask**: McCabe=`5`, WCET=`1.66 μs`, Chama 9 funções
- **commandProcessingTask**: McCabe=`7`, WCET=`1.69 μs`, Chama 12 funções
- **eTaskGetState**: McCabe=`12`, WCET=`1.28 μs`, Chama 3 funções
- **keyboard_task**: McCabe=`3`, WCET=`0.53 μs`, Chama 6 funções
- **pcTaskGetName**: McCabe=`3`, WCET=`0.26 μs`, Chama 1 funções
- **prvAddCurrentTaskToDelayedList**: McCabe=`5`, WCET=`1.03 μs`, Chama 2 funções
- **prvAddNewTaskToReadyList**: McCabe=`8`, WCET=`1.34 μs`, Chama 4 funções
- **prvCheckTasksWaitingTermination**: McCabe=`2`, WCET=`0.45 μs`, Chama 4 funções
- **prvCreateIdleTasks**: McCabe=`2`, WCET=`0.50 μs`, Chama 2 funções
- **prvIdleTask**: McCabe=`2`, WCET=`0.18 μs`, Chama 2 funções
- **prvInitialiseNewTask**: McCabe=`6`, WCET=`1.18 μs`, Chama 4 funções
- **prvInitialiseTaskLists**: McCabe=`2`, WCET=`0.57 μs`, Chama 1 funções
- **prvListTasksWithinSingleList**: McCabe=`5`, WCET=`0.82 μs`, Chama 1 funções
- **prvProcessTimerOrBlockTask**: McCabe=`6`, WCET=`0.86 μs`, Chama 6 funções
- **prvResetNextTaskUnblockTime**: McCabe=`2`, WCET=`0.29 μs`, Chama 0 funções
- **prvTaskCheckFreeStackSpace**: McCabe=`2`, WCET=`0.14 μs`, Chama 0 funções
- **prvTaskExitError**: McCabe=`1`, WCET=`0.06 μs`, Chama 1 funções
- **prvTimerTask**: McCabe=`1`, WCET=`0.18 μs`, Chama 3 funções
- **pvTaskIncrementMutexHeldCount**: McCabe=`2`, WCET=`0.13 μs`, Chama 0 funções
- **sanitizeTaskName**: McCabe=`7`, WCET=`0.63 μs`, Chama 0 funções
- **timer_task**: McCabe=`3`, WCET=`0.66 μs`, Chama 3 funções
- **tud_task_ext**: McCabe=`15`, WCET=`3.30 μs`, Chama 12 funções
- **ulTaskGenericNotifyTake**: McCabe=`6`, WCET=`1.24 μs`, Chama 6 funções
- **uxTaskGetNumberOfTasks**: McCabe=`1`, WCET=`0.06 μs`, Chama 0 funções
- **uxTaskGetSystemState**: McCabe=`4`, WCET=`1.06 μs`, Chama 4 funções
- **uxTaskResetEventItemValue**: McCabe=`1`, WCET=`0.16 μs`, Chama 0 funções
- **vApplicationGetIdleTaskMemory**: McCabe=`1`, WCET=`0.14 μs`, Chama 0 funções
- **vApplicationGetTimerTaskMemory**: McCabe=`1`, WCET=`0.14 μs`, Chama 0 funções
- **vDoorStateMqttTask**: McCabe=`1`, WCET=`1.18 μs`, Chama 7 funções
- **vGpsMqttTask**: McCabe=`2`, WCET=`1.72 μs`, Chama 7 funções
- **vGpsTask**: McCabe=`1`, WCET=`1.25 μs`, Chama 7 funções
- **vHumidityMqttTask**: McCabe=`1`, WCET=`0.89 μs`, Chama 5 funções
- **vMenuOledTask**: McCabe=`16`, WCET=`2.65 μs`, Chama 7 funções
- **vNetworkPollTask**: McCabe=`4`, WCET=`1.25 μs`, Chama 9 funções
- **vOledStatusTask**: McCabe=`1`, WCET=`0.38 μs`, Chama 4 funções
- **vPortStartFirstTask**: McCabe=`1`, WCET=`0.30 μs`, Chama 0 funções
- **vRTOSMonitorTask**: McCabe=`3`, WCET=`1.82 μs`, Chama 13 funções
- **vTaskDelay**: McCabe=`4`, WCET=`0.52 μs`, Chama 6 funções
- **vTaskGetInfo**: McCabe=`8`, WCET=`1.26 μs`, Chama 6 funções
- **vTaskGetRunTimeStats**: McCabe=`5`, WCET=`1.18 μs`, Chama 7 funções
- **vTaskInternalSetTimeOutState**: McCabe=`1`, WCET=`0.13 μs`, Chama 0 funções
- **vTaskMissedYield**: McCabe=`1`, WCET=`0.07 μs`, Chama 0 funções
- **vTaskPlaceOnEventList**: McCabe=`2`, WCET=`0.33 μs`, Chama 3 funções
- **vTaskPlaceOnEventListRestricted**: McCabe=`3`, WCET=`0.58 μs`, Chama 2 funções
- **vTaskPlaceOnUnorderedEventList**: McCabe=`3`, WCET=`0.75 μs`, Chama 2 funções
- **vTaskPriorityDisinheritAfterTimeout**: McCabe=`10`, WCET=`1.27 μs`, Chama 2 funções
- **vTaskRemoveFromUnorderedEventList**: McCabe=`7`, WCET=`1.54 μs`, Chama 1 funções
- **vTaskStartScheduler**: McCabe=`4`, WCET=`0.70 μs`, Chama 6 funções
- **vTaskSuspendAll**: McCabe=`1`, WCET=`0.09 μs`, Chama 0 funções
- **vTaskSwitchContext**: McCabe=`10`, WCET=`1.95 μs`, Chama 6 funções
- **vTemperatureHumidityTask**: McCabe=`3`, WCET=`2.40 μs`, Chama 12 funções
- **vTemperatureMqttTask**: McCabe=`1`, WCET=`0.94 μs`, Chama 6 funções
- **vTiltMqttTask**: McCabe=`2`, WCET=`1.02 μs`, Chama 5 funções
- **vTiltTask**: McCabe=`2`, WCET=`1.05 μs`, Chama 9 funções
- **watchdogSupervisorTask**: McCabe=`3`, WCET=`0.81 μs`, Chama 7 funções
- **watchdogTaskInit**: McCabe=`4`, WCET=`0.83 μs`, Chama 3 funções
- **xTaskCheckForTimeOut**: McCabe=`8`, WCET=`1.18 μs`, Chama 4 funções
- **xTaskCreate**: McCabe=`3`, WCET=`0.79 μs`, Chama 5 funções
- **xTaskCreateStatic**: McCabe=`4`, WCET=`1.10 μs`, Chama 4 funções
- **xTaskGetCurrentTaskHandle**: McCabe=`1`, WCET=`0.06 μs`, Chama 0 funções
- **xTaskGetSchedulerState**: McCabe=`3`, WCET=`0.25 μs`, Chama 0 funções
- **xTaskGetTickCount**: McCabe=`1`, WCET=`0.06 μs`, Chama 0 funções
- **xTaskIncrementTick**: McCabe=`14`, WCET=`2.52 μs`, Chama 2 funções
- **xTaskPriorityDisinherit**: McCabe=`7`, WCET=`1.20 μs`, Chama 2 funções
- **xTaskPriorityInherit**: McCabe=`7`, WCET=`1.30 μs`, Chama 1 funções
- **xTaskRemoveFromEventList**: McCabe=`7`, WCET=`1.68 μs`, Chama 1 funções
- **xTaskResumeAll**: McCabe=`14`, WCET=`2.38 μs`, Chama 6 funções
- **xTimerCreateTimerTask**: McCabe=`3`, WCET=`0.68 μs`, Chama 4 funções
- **xTimerGenericCommandFromTask**: McCabe=`5`, WCET=`0.80 μs`, Chama 3 funções

### Callgraph (amostra de arestas)
- `hold_non_core0_in_bootrom` → `data_cpy`
- `frame_dummy` → `register_tm_clones`
- `indata_cb` → `__wrap___aeabi_memcpy`
- `indata_cb` → `log_write`
- `indata_cb` → `processCommandBuzzer`
- `indata_cb` → `processCommandDoor`
- `indata_cb` → `processCommandVentilation`
- `inpub_cb` → `log_write`
- `inpub_cb` → `__wrap_snprintf`
- `inpub_cb` → `strcmp`
- `add_repeating_timer_ms` → `alarm_pool_get_default`
- `add_repeating_timer_ms` → `__wrap___aeabi_lmul`
- `add_repeating_timer_ms` → `alarm_pool_add_repeating_timer_us`
- `dns_check_callback` → `ip4addr_ntoa`
- `dns_check_callback` → `log_write`
- `dns_check_callback` → `mqtt_client_connect`
- `subscribeToCommandTopics` → `__wrap_snprintf`
- `subscribeToCommandTopics` → `mqtt_sub_unsub`
- `subscribeToCommandTopics` → `log_write`
- `mqtt_connection_callback` → `log_write`
- `mqtt_connection_callback` → `commandMqttInit`
- `mqtt_connection_callback` → `subscribeToCommandTopics`
- `__static_initialization_and_destruction_0()` → `I2C::I2C(i2c_inst*, unsigned int, unsigned int)`
- `main` → `stdio_init_all`
- `main` → `log_set_level`
- `main` → `gpio_init`
- `main` → `add_repeating_timer_ms`
- `main` → `log_write`
- `main` → `sleep_ms`
- `main` → `cyw43_arch_init`
- ... e mais 2815 arestas

## Notas
- Análise offline do ELF realizada com sucesso.
- O WCET estimado é baseado em contagem de ciclos de instrução (pior caso).
