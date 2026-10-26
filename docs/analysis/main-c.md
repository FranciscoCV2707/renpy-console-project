# Análisis de `main.c` y `modules/` — lógica portable vs PS1 (T-101)
> Documento generado por T-101 (agente beam). Solo lectura del repo hermano `E:\Dev\vn-engine-ps1`; no se modificó ningún archivo fuera de este repo.
> Fuentes: `vn-engine-ps1/app/main.c`, `app/app.h`, `app/game.h`, `app/ui_text.h`, `modules/*.c`, `modules/special.h`; contrato `engine/core/vn_platform.h`, `docs/core-api.md`, `PLAN.md` §§3-4.
## 1. Alcance y método
- Se listó cada función de `app/main.c` (94) y de `modules/*.c` (42) con su rango de líneas.
- Clasificación:
  - **Portable**: el cuerpo no llama a ninguna primitiva de hardware (`video_*`, `img_*`, `res_*`, `audio_*`, `cd_*`, `save_*`, `input_*`, `psx*`, `VSync`, `printf`).
  - **Mixta**: contiene al menos una de esas llamadas; se indican con `archivo:línea`. No hay funciones 100 % hardware: toda llamada hardware convive con lógica.
- Los conteos por función se obtuvieron con un escaneo automático de las llamadas seguidas de `(`; las variables globales de módulos (`cd_sync_vblanks`, `res_trace_tag`) no se cuentan como llamadas.
## 2. Resumen
| Archivo | Funciones | Portables | Mixtas |
|---|---:|---:|---:|
| `app/main.c` | 94 | 47 | 47 |
| `modules/canvas.c` | 6 | 4 | 2 |
| `modules/credits.c` | 5 | 3 | 2 |
| `modules/fmv.c` | 11 | 5 | 6 |
| `modules/keyboard.c` | 7 | 4 | 3 |
| `modules/phone.c` | 9 | 6 | 3 |
| `modules/strips.c` | 4 | 2 | 2 |
| **Total** | **136** | **71** | **65** |

`main.c` concentra la máquina de estados, el bucle principal y el bootstrap de la PS1; por eso la mitad de sus funciones son mixtas. Los módulos especiales (`fmv.c`) son los más dependientes del hardware.
## 3. Funciones de `app/main.c`
| Función | Líneas | Clase | Llamadas hardware (`main.c:línea`) |
|---|---|---|---|
| `fatal` | 126-137 | Mixta | `printf` (L130), `video_rect` (L132), `video_flip` (L133), `VSync` (L136) |
| `rd16` | 139-142 | Portable | — |
| `rd32` | 144-147 | Portable | — |
| `random_below` | 149-153 | Portable | — |
| `seen_get` | 156-159 | Portable | — |
| `seen_set` | 161-165 | Portable | — |
| `load_game_tables` | 168-283 | Mixta | `cd_read_file` (L171) |
| `gallery_mark` | 285-301 | Portable | — |
| `chapter_loader` | 303-307 | Portable | — |
| `camera_on` | 322-325 | Portable | — |
| `camera_update` | 327-341 | Mixta | `video_frames` (L329) |
| `cam_sx` | 343-346 | Portable | — |
| `cam_sy` | 348-351 | Portable | — |
| `camera_reset` | 354-358 | Portable | — |
| `notify` | 360-465 | Mixta | `video_frames` (L383), `video_frames` (L386), `audio_music_play` (L440), `audio_music_queue` (L443), `audio_music_stop` (L446), `audio_ambient_play` (L449), `audio_ambient_stop` (L452), `audio_sfx_play` (L456), `audio_sfx_stop_fade` (L459), `audio_volume` (L462) |
| `op_size` | 467-475 | Portable | — |
| `log_stall` | 485-502 | Portable | — |
| `add_image` | 509-519 | Portable | — |
| `look_ahead` | 524-570 | Mixta | `audio_preload` (L546), `audio_sfx_missing` (L547), `audio_ambient_missing` (L549) |
| `prefetch_next` | 575-591 | Mixta | `res_prefetch_busy` (L580), `res_touch` (L584), `res_have` (L585), `audio_cd_paused` (L587), `res_prefetch` (L588) |
| `anim_sounds` | 594-621 | Mixta | `video_frames` (L608), `audio_sfx_play` (L616) |
| `bg_align` | 625-651 | Mixta | `video_frames` (L628) |
| `covers_view` | 654-658 | Portable | — |
| `scene_sync` | 660-691 | Mixta | `res_new_scene` (L669), `res_touch` (L674), `res_touch` (L676), `res_get` (L678), `res_get` (L684), `res_preload` (L689) |
| `ease256` | 715-728 | Portable | — |
| `begin_transition` | 730-777 | Mixta | `res_reserve_snapshot` (L757), `video_snapshot` (L758) |
| `end_transition` | 779-787 | Mixta | `res_release_snapshot` (L782) |
| `update_transition` | 789-793 | Portable | — |
| `transition_offset` | 796-810 | Portable | — |
| `move_position` | 813-831 | Portable | — |
| `transition_brightness` | 836-850 | Portable | — |
| `draw_transition` | 852-888 | Mixta | `video_snapshot_draw` (L864), `video_snapshot_draw` (L870), `video_rect` (L872), `video_rect` (L878), `video_snapshot_draw` (L880), `video_rect` (L882), `video_rect` (L885) |
| `draw_bg` | 890-920 | Mixta | `video_rect` (L893), `video_rect` (L898), `img_draw_big` (L913), `img_draw_ex` (L915), `img_draw_flip` (L917) |
| `draw_solid` | 922-935 | Mixta | `video_rect` (L934) |
| `draw_scene` | 937-996 | Mixta | `video_frames` (L950), `img_draw_ex_rot` (L982), `img_draw_ex_rot` (L985), `video_clip_scene` (L990), `video_clip_scene` (L995) |
| `draw_box` | 1000-1018 | Mixta | `video_rect` (L1006), `video_rect` (L1008), `video_frames` (L1016), `video_triangle_down` (L1017) |
| `update_box` | 1021-1032 | Portable | — |
| `option_lines` | 1034-1042 | Portable | — |
| `menu_begin` | 1044-1059 | Portable | — |
| `draw_imgmenu` | 1063-1093 | Mixta | `img_draw_big` (L1069), `img_draw` (L1071), `img_draw_ex` (L1077), `video_rect` (L1087), `video_rect` (L1088), `video_rect` (L1089), `video_rect` (L1090) |
| `draw_menu` | 1095-1130 | Mixta | `video_rect` (L1103), `video_triangle_down` (L1126) |
| `start_say` | 1135-1143 | Portable | — |
| `run_vm` | 1145-1202 | Mixta | `audio_batch_begin` (L1149), `video_frames` (L1151), `VSync` (L1159), `VSync` (L1162), `audio_cd_paused` (L1170), `res_prefetch` (L1173), `printf` (L1195), `audio_batch_end` (L1201) |
| `clear_scene` | 1204-1210 | Portable | — |
| `begin` | 1212-1227 | Mixta | `audio_stop_all` (L1215) |
| `update_dev` | 1232-1260 | Mixta | `input_pressed` (L1236), `input_pressed` (L1238), `input_pressed` (L1240), `input_pressed` (L1244) |
| `draw_dev` | 1262-1282 | Mixta | `video_rect` (L1266), `video_triangle_down` (L1277) |
| `wr16` | 1308-1312 | Portable | — |
| `wr32` | 1314-1318 | Portable | — |
| `progress_to_buf` | 1325-1334 | Portable | — |
| `progress_from_buf` | 1336-1351 | Mixta | `audio_set_levels` (L1350) |
| `newest_slot` | 1353-1361 | Portable | — |
| `show_now` | 1365-1374 | Mixta | `video_rect` (L1370), `video_flip` (L1372) |
| `write_card` | 1391-1399 | Mixta | `save_write` (L1397) |
| `save_slot` | 1401-1426 | Mixta | `save_slot` (L1401), `audio_music_current` (L1415), `audio_ambient_current` (L1417) |
| `load_slot` | 1428-1473 | Mixta | `audio_stop_all` (L1434), `audio_music_play` (L1461), `audio_ambient_play` (L1466) |
| `notice` | 1487-1492 | Portable | — |
| `draw_center` | 1495-1512 | Portable | — |
| `draw_list` | 1515-1526 | Mixta | `video_triangle_down` (L1523) |
| `list_input` | 1529-1540 | Mixta | `input_pressed` (L1531), `input_pressed` (L1533), `input_pressed` (L1535), `input_pressed` (L1537) |
| `panel` | 1542-1546 | Mixta | `video_rect` (L1544), `video_rect` (L1545) |
| `extras_list` | 1549-1557 | Portable | — |
| `go_title` | 1559-1569 | Mixta | `audio_stop_all` (L1563) |
| `open_slots` | 1573-1579 | Portable | — |
| `open_options` | 1581-1587 | Portable | — |
| `title_rows` | 1590-1598 | Portable | — |
| `update_title` | 1600-1642 | Mixta | `input_down` (L1604), `input_down` (L1604), `input_pressed` (L1604) |
| `draw_title` | 1644-1664 | Mixta | `res_get` (L1646), `img_draw` (L1656), `res_get` (L1659), `img_draw` (L1662) |
| `update_pause_menu` | 1670-1705 | Mixta | `input_pressed` (L1674), `video_frames` (L1674) |
| `do_save` | 1707-1719 | Mixta | `save_slot` (L1711) |
| `update_slots` | 1721-1746 | Portable | — |
| `draw_slots` | 1748-1773 | Mixta | `video_triangle_down` (L1769) |
| `update_confirm` | 1775-1791 | Mixta | `input_pressed` (L1777), `input_pressed` (L1777), `input_pressed` (L1777), `input_pressed` (L1777), `input_pressed` (L1779), `input_pressed` (L1779), `input_pressed` (L1783) |
| `draw_confirm` | 1793-1799 | Portable | — |
| `update_options` | 1801-1824 | Mixta | `input_pressed` (L1805), `input_pressed` (L1807), `input_pressed` (L1809), `input_pressed` (L1813), `audio_set_levels` (L1817), `input_pressed` (L1818), `input_pressed` (L1818) |
| `draw_bar` | 1826-1833 | Mixta | `video_rect` (L1832) |
| `draw_options` | 1835-1843 | Portable | — |
| `gallery_seen_at` | 1845-1848 | Portable | — |
| `gallery_first_image` | 1850-1858 | Portable | — |
| `video_at` | 1861-1869 | Mixta | `video_at` (L1861) |
| `update_gallery` | 1871-1890 | Mixta | `input_pressed` (L1875), `input_pressed` (L1877), `video_at` (L1879), `input_pressed` (L1880), `input_pressed` (L1886) |
| `draw_gallery` | 1892-1924 | Mixta | `res_new_scene` (L1900), `res_get` (L1901), `img_draw_big` (L1907), `img_draw` (L1909), `video_at` (L1911), `video_rect` (L1912), `video_rect` (L1916), `video_clip_scene` (L1919) |
| `update_extras` | 1926-1940 | Portable | — |
| `draw_extras` | 1942-1952 | Portable | — |
| `begin_special` | 1955-1966 | Portable | — |
| `finish_game` | 1969-1974 | Portable | — |
| `autoplay_step` | 1980-2024 | Mixta | `res_prefetch_busy` (L1984), `audio_loading` (L1984), `res_prefetch_busy` (L1997), `audio_loading` (L1997), `res_prefetch_busy` (L2005), `audio_loading` (L2005) |
| `skip_step` | 2027-2048 | Portable | — |
| `update_say` | 2050-2073 | Mixta | `input_pressed` (L2052), `res_prefetch_busy` (L2055) |
| `update_imgmenu` | 2075-2085 | Mixta | `input_pressed` (L2077), `input_pressed` (L2077), `input_pressed` (L2079), `input_pressed` (L2079), `input_pressed` (L2081) |
| `update_menu` | 2087-2101 | Mixta | `input_pressed` (L2093), `input_pressed` (L2095), `input_pressed` (L2097) |
| `draw_debug` | 2103-2109 | Portable | — |
| `capture` | 2112-2116 | Portable | — |
| `main` | 2118-2371 | Mixta | `video_init` (L2123), `cd_init` (L2124), `audio_init` (L2125), `cd_find` (L2130), `input_init` (L2132), `cd_find` (L2138), `cd_read_file` (L2142), `cd_read_file` (L2149), `save_set_icon` (L2150), `cd_find` (L2156), `cd_read_file` (L2157), `input_set_script` (L2158), `video_flip` (L2168), `input_raw_down` (L2170), `save_read` (L2172), `VSync` (L2174), `VSync` (L2179), `video_flip` (L2183), `VSync` (L2188), `input_update` (L2193), `audio_update` (L2194), `input_pressed` (L2200), `input_pressed` (L2202), `input_pressed` (L2205), `video_frames` (L2207), `input_pressed` (L2216), `input_pressed` (L2218), `input_pressed` (L2241), `input_pressed` (L2248), `input_pressed` (L2279), `input_pressed` (L2279), `res_tick` (L2291), `video_unclip` (L2352), `VSync` (L2354), `video_flip` (L2368) |
## 4. Funciones de `modules/*.c`
### 4.1 `modules/canvas.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `canvas_begin` | 24-30 | Portable | — |
| `stamp` | 32-43 | Portable | — |
| `canvas_update` | 45-69 | Mixta | `input_down` (L47), `input_down` (L49), `input_down` (L51), `input_down` (L53), `input_pressed` (L56), `input_pressed` (L58), `input_down` (L62), `input_pressed` (L66), `input_pressed` (L68) |
| `canvas_draw` | 72-92 | Mixta | `video_rect` (L76), `video_rect` (L77), `video_rect` (L86), `video_rect` (L91) |
| `canvas_bits` | 97-101 | Portable | — |
| `canvas_load` | 104-108 | Portable | — |
### 4.2 `modules/credits.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `credits_clear` | 17-20 | Portable | — |
| `credits_add` | 22-32 | Portable | — |
| `credits_begin` | 34-40 | Portable | — |
| `credits_update` | 42-48 | Mixta | `input_down` (L46), `input_pressed` (L47) |
| `credits_draw` | 50-63 | Mixta | `video_rect` (L54) |
### 4.3 `modules/fmv.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `fmv_select` | 62-65 | Portable | — |
| `fmv_dma_idle` | 69-71 | Portable | — |
| `fmv_buffers` | 74-90 | Mixta | `res_borrow_cache` (L77) |
| `sector_handler` | 94-126 | Mixta | `VSync` (L99) |
| `mdec_dma_handler` | 130-141 | Portable | — |
| `cd_event_handler` | 143-152 | Mixta | `cd_event_handler` (L143) |
| `fmv_wait_frame` | 155-173 | Mixta | `VSync` (L157), `VSync` (L160), `input_update` (L165), `input_pressed` (L166) |
| `fmv_play` | 175-248 | Mixta | `cd_wait` (L186), `audio_video_begin` (L187), `VSync` (L203), `VSync` (L223), `audio_video_end` (L247), `VSync` (L247) |
| `fmv_begin` | 250-267 | Mixta | `cd_find` (L258) |
| `fmv_update` | 270-274 | Portable | — |
| `fmv_draw` | 276-278 | Portable | — |
### 4.4 `modules/keyboard.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `kb_begin` | 35-40 | Portable | — |
| `kb_type` | 42-50 | Portable | — |
| `kb_erase` | 52-62 | Portable | — |
| `kb_update` | 64-100 | Mixta | `input_pressed` (L66), `input_pressed` (L68), `input_pressed` (L70), `input_pressed` (L72), `input_pressed` (L74), `input_pressed` (L76), `input_pressed` (L78), `input_pressed` (L80) |
| `kb_key` | 102-106 | Mixta | `video_rect` (L105) |
| `kb_draw` | 108-125 | Mixta | `video_frames` (L115), `video_rect` (L116), `video_rect` (L117) |
| `kb_autoplay` | 128-143 | Portable | — |
### 4.5 `modules/phone.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `phone_clear` | 21-24 | Portable | — |
| `phone_add` | 26-34 | Portable | — |
| `text_lines` | 36-44 | Portable | — |
| `bubble_h` | 47-58 | Mixta | `res_get` (L52) |
| `phone_total` | 60-67 | Portable | — |
| `phone_max_scroll` | 69-74 | Portable | — |
| `phone_begin` | 76-82 | Portable | — |
| `phone_update` | 84-93 | Mixta | `input_down` (L86), `input_down` (L88), `input_down` (L90), `input_pressed` (L92) |
| `phone_draw` | 95-139 | Mixta | `res_new_scene` (L99), `video_rect` (L100), `video_rect` (L107), `res_get` (L110), `img_draw` (L113), `video_clip_scene` (L138) |
### 4.6 `modules/strips.c`
| Función | Líneas | Clase | Llamadas hardware (`archivo:línea`) |
|---|---|---|---|
| `strips_setup` | 15-19 | Portable | — |
| `strips_begin` | 21-27 | Portable | — |
| `strips_update` | 29-39 | Mixta | `input_down` (L31), `input_down` (L33), `input_down` (L35), `input_pressed` (L38) |
| `strips_draw` | 41-72 | Mixta | `res_new_scene` (L45), `res_get` (L47), `img_draw` (L50), `video_clip_scene` (L52), `video_rect` (L59), `video_rect` (L60), `video_frames` (L65), `video_triangle_down` (L66) |
## 5. Llamadas de hardware de `main.c` + `modules/`, agrupadas por módulo
### video (PS1 GPU/VSync) — 84 llamadas
| Llamada | Veces |
|---|---:|
| `VSync` | 13 |
| `video_at` | 3 |
| `video_clip_scene` | 5 |
| `video_flip` | 5 |
| `video_frames` | 12 |
| `video_init` | 1 |
| `video_rect` | 34 |
| `video_snapshot` | 1 |
| `video_snapshot_draw` | 3 |
| `video_triangle_down` | 6 |
| `video_unclip` | 1 |

### img (VRAM/imágenes) — 14 llamadas
| Llamada | Veces |
|---|---:|
| `img_draw` | 6 |
| `img_draw_big` | 3 |
| `img_draw_ex` | 2 |
| `img_draw_ex_rot` | 2 |
| `img_draw_flip` | 1 |

### res (gestor de recursos/VRAM) — 28 llamadas
| Llamada | Veces |
|---|---:|
| `res_borrow_cache` | 1 |
| `res_get` | 8 |
| `res_have` | 1 |
| `res_new_scene` | 4 |
| `res_prefetch` | 2 |
| `res_prefetch_busy` | 5 |
| `res_preload` | 1 |
| `res_release_snapshot` | 1 |
| `res_reserve_snapshot` | 1 |
| `res_tick` | 1 |
| `res_touch` | 3 |

### audio (SPU/CD-XA) — 32 llamadas
| Llamada | Veces |
|---|---:|
| `audio_ambient_current` | 1 |
| `audio_ambient_missing` | 1 |
| `audio_ambient_play` | 2 |
| `audio_ambient_stop` | 1 |
| `audio_batch_begin` | 1 |
| `audio_batch_end` | 1 |
| `audio_cd_paused` | 2 |
| `audio_init` | 1 |
| `audio_loading` | 3 |
| `audio_music_current` | 1 |
| `audio_music_play` | 2 |
| `audio_music_queue` | 1 |
| `audio_music_stop` | 1 |
| `audio_preload` | 1 |
| `audio_set_levels` | 2 |
| `audio_sfx_missing` | 1 |
| `audio_sfx_play` | 2 |
| `audio_sfx_stop_fade` | 1 |
| `audio_stop_all` | 3 |
| `audio_update` | 1 |
| `audio_video_begin` | 1 |
| `audio_video_end` | 1 |
| `audio_volume` | 1 |

### cd (lectura de disco) — 11 llamadas
| Llamada | Veces |
|---|---:|
| `cd_event_handler` | 1 |
| `cd_find` | 4 |
| `cd_init` | 1 |
| `cd_read_file` | 4 |
| `cd_wait` | 1 |

### input (mando) — 80 llamadas
| Llamada | Veces |
|---|---:|
| `input_down` | 14 |
| `input_init` | 1 |
| `input_pressed` | 61 |
| `input_raw_down` | 1 |
| `input_set_script` | 1 |
| `input_update` | 2 |

### save (memory card) — 5 llamadas
| Llamada | Veces |
|---|---:|
| `save_read` | 1 |
| `save_set_icon` | 1 |
| `save_slot` | 2 |
| `save_write` | 1 |

### debug — 2 llamadas
| Llamada | Veces |
|---|---:|
| `printf` | 2 |

## 6. Estado global (`static` de `main.c`)
Variables de ámbito de archivo (línea en `main.c`), agrupadas por subsistema. También hay un `static uint8_t autotest[16384]` local dentro de `main()` (L2153) para el script de prueba.
| Línea | Variable(s) | Subsistema | Nota |
|---:|---|---|---|
| 60 | `file_buf[16 KiB]` | Guardado / disco | buffer de carga de archivos |
| 61 | `speakers[]` | Datos del juego (GAME.BIN) | tabla de hablantes |
| 62 | `speaker_count` | Datos del juego (GAME.BIN) |  |
| 63 | `pos_x[], pos_y[]` | Escena / posiciones | posiciones ATL |
| 64 | `pos_count` | Escena / posiciones |  |
| 65 | `start_chapter` | Arranque | capítulo inicial |
| 66 | `start_offset` | Arranque | offset inicial |
| 68 | `vm` | VM | máquina virtual |
| 69 | `state` | Máquina de estados | estado actual |
| 70 | `run` | Texto | ejecución de texto |
| 71 | `scene_dirty, show_box, debug` | Escena / texto / depuración |  |
| 76 | `win_auto, win_on, box_level` | Texto / caja | ventana automática |
| 77 | `snap_box` | Transición | caja en la copia |
| 78 | `pause_left, say_seen_before` | Texto / pausa |  |
| 79 | `bg_start` | Escena | cuadro de aparición del fondo |
| 80 | `seen[]` | Progreso | líneas vistas |
| 81 | `endings_mask, bonus_mask` | Progreso | finales y extras vistos |
| 82 | `gallery_image[]` | Galería |  |
| 83 | `gallery_index[]` | Galería |  |
| 84 | `gallery_pairs, gallery_count` | Galería |  |
| 85 | `gallery_seen[]` | Galería / progreso |  |
| 91 | `video_count` | Galería de vídeo |  |
| 92 | `video_slot[], video_file[]` | Galería de vídeo |  |
| 93 | `video_unlock[]` | Galería de vídeo |  |
| 94 | `special_return` | Pantallas especiales | retorno al terminar |
| 97 | `dev_count, dev_chapter` | Menú de desarrollo |  |
| 98 | `dev_offset[]` | Menú de desarrollo |  |
| 99 | `dev_var[], dev_value[]` | Menú de desarrollo |  |
| 100 | `dev_name[][]` | Menú de desarrollo |  |
| 103 | `skip_mode, eat_cross` | Modo saltar |  |
| 104 | `dev_session` | Modo saltar | partida desde desarrollo |
| 107 | `logo_image, lock_image` | Datos UI (GAME.BIN) |  |
| 108 | `ending_image[]` | Datos UI | imagen por final |
| 109 | `ending_count` | Datos UI |  |
| 110 | `chapter_name[][]` | Datos UI |  |
| 111 | `extra_count` | Capítulos extra |  |
| 112 | `extra_chapter[]` | Capítulos extra |  |
| 113 | `extra_offset[]` | Capítulos extra |  |
| 114 | `extra_name[][]` | Capítulos extra |  |
| 115 | `special` | Pantallas especiales | pantalla abierta |
| 118 | `music_level, sfx_level` | Audio | niveles de volumen |
| 119 | `play_frames` | Partida | tiempo de la partida |
| 120 | `playing_extra` | Partida | es capítulo extra |
| 121 | `autosave_pending` | Guardado | autosave pendiente |
| 123 | `menu_cursor, menu_top, menu_order[]` | Menús |  |
| 124 | `rng_state` | Menús / aleatorio |  |
| 319 | `cam_z, cam_x, cam_y` | Cámara / escena | zoom y desplazamiento |
| 320 | `cam_z0..cam_curve` | Cámara / escena | animación de cámara |
| 506 | `near_sfx_missing` | Prefetch de audio | efecto no cargado |
| 507 | `say_prefetched` | Prefetch | ya revisado lo siguiente |
| 708 | `trans_type..snap_y` | Transición | estado de la transición |
| 709 | `scene_dx, scene_dy` | Escena | sacudidas |
| 710 | `last_x[], last_y[]` | Transición / sprites | posición anterior |
| 711 | `last_tag[], last_valid[]` | Transición / sprites |  |
| 712 | `from_x[], from_y[]` | Transición / sprites | origen de la animación |
| 713 | `from_edge[]` | Transición / sprites | borde de entrada |
| 1304 | `save_buf[]` | Guardado | buffer de la memory card |
| 1305 | `card_state` | Guardado | estado de la tarjeta |
| 1306 | `save_number` | Guardado | número de guardado |
| 1389 | `card_disabled` | Guardado | sin memory card |
| 1479 | `ui_cursor, ui_mode, ui_slot, ui_changed, gallery_pos` | UI / menús |  |
| 1480 | `ui_back` | UI / menús | retorno |
| 1481 | `pause_from` | Pausa | estado al abrir pausa |
| 1482 | `notice_text` | UI / avisos |  |
| 1483 | `notice_next` | UI / avisos | estado siguiente |
| 1484 | `confirm_text` | UI / confirmación |  |
| 1485 | `confirm_action, confirm_yes` | UI / confirmación |  |
| 1668 | `pause_opened` | Pausa | cuadro de apertura |
| 1978 | `autoplay_started, autoplay_menus` | Prueba automática |  |

También son estado global no `static`: `decode_vblanks` (L482, `volatile uint32_t`, contador de cuadros de decodificación) y los arrays de módulos (`cv`, `ph`, `frames`, etc.) en `modules/`.
## 7. Propuesta de operaciones nuevas para `VnPlatformOps` (no se edita el contrato)
El núcleo actual solo expone archivos y fuente. Para mover `main.c` al núcleo hacen falta, como mínimo, las siguientes operaciones. Se agrupan por subsistema; los nombres son propuesta.
### Gráficos
- `clear`, `draw_sprite`, `present` ya existen.
- `draw_rect(layer, x, y, w, h, r, g, b, alpha)` — `video_rect` (34 usos).
- `draw_triangle_down(layer, x, y, w, h, r, g, b)` — `video_triangle_down` (6).
- `clip_scene()` / `unclip()` — `video_clip_scene` (5) y `video_unclip` (1).
- `snapshot_save()` / `snapshot_restore()` / `snapshot_draw(layer, ...)` — `video_snapshot*` (5) para transiciones.
- `get_frame_count()` — `video_frames` (12), base de tiempo de cámara, transiciones y caja.
- `flip()` ya está cubierto por `present`; si se necesita intercambio explícito, mantener `present`.
### Imágenes (`img`/`res`)
- `draw_image(id, layer, x, y, w, h, flip, zoom, angle, r, g, b)` — `img_draw*` (13).
- `scene_begin()` — `res_new_scene` (4): reinicia el uso de VRAM de la escena.
- `image_get(id)` o, mejor, que el backend resuelva ids dentro de `draw_image`.
- `prefetch(ids, n)` / `prefetch_busy()` / `touch(id)` / `have(id)` — prefetch de escenas siguientes (8 usos).
- `tick_resources()` — `res_tick` (1), ya llamado en el bucle.
- `borrow_cache(&bytes)` — `res_borrow_cache` (1) para FMV.
- `reserve_snapshot()` / `release_snapshot()` — transiciones (2).
### Audio
- `play_music(id, loop)`, `queue_music(id)`, `stop_music(fade)`, `play_ambient(id, loop)`, `stop_ambient(fade)`, `play_sfx(id)`, `stop_sfx(id)`, `set_audio_levels(music, sfx)`, `stop_all_audio()`, `audio_update()`, `audio_cd_paused()`, `audio_preload()`, `audio_loading()`, `audio_video_begin/end()`.
### Entrada
- `input_init(has_card)`, `input_update()`, `input_pressed(mask)`, `input_down(mask)`, `input_raw_down(mask)`, `input_set_script(data, count)` (autotest).
### Disco / archivos
- `file_size`/`file_read` ya existen. Falta `cd_init()` (bootstrap, puede ser del backend), `cd_find(name)` (se cubre con `file_size`), `cd_wait()` y contadores `cd_sync_vblanks`/`cd_wait_vblanks` (hoy variables del módulo `cd`).
- `wait_vblanks(n)` y `get_vblank_count()` para el tiempo de VSync (`VSync`, 13 usos) en lugar de llamar a la BIOS.
### Guardado
- `card_read(buf, size)`, `card_write(buf, size)`, `card_set_icon(buf)`; el resto (`save_slot`, `load_slot`, `progress_to/from_buf`) es lógica que puede vivir en el núcleo usando `save_buf` propio.
### Depuración
- `log` ya existe; `printf` de depuración se sustituye por `log`.
## 8. Orden propuesto de extracción (pasos < ~400 líneas)
Cada paso debe compilar y pasar `pytest` (prueba de host) antes del siguiente. Los números de líneas son de `main.c` salvo que se indique.
| Paso | Contenido | Destino |
|---|---|---|
| Paso 1 — Utilidades puras | Mover funciones sin llamadas hardware: `rd16`, `rd32`, `random_below`, `seen_get/set`, `camera_on`, `cam_sx/sy`, `camera_reset`, `ease256`, `covers_view`, `op_size`, `update_box`, `option_lines`, `menu_begin`, `start_say`, `clear_scene`, `wr16/32`, `newest_slot`, `notice`, `draw_center`, `extras_list`, `open_slots/options`, `title_rows`. ~260 líneas. | `engine/core/vn_util.c` |
| Paso 2 — Datos de GAME.BIN y progreso | Mover `load_game_tables` (L168-283, 116 l.) usando `file_read`; `gallery_mark` (L285-301); `chapter_loader` (L303-307); `progress_to_buf/from_buf` (L1325-1351) con `card_read/write` por ops. ~180 líneas. | `engine/core/vn_game_data.c` |
| Paso 3 — Cámara, transiciones y matemática de escena | Mover `camera_update`, `bg_align`, `begin/end/update_transition`, `transition_offset/brightness`, `move_position`, `draw_transition` (parte lógica; el dibujo queda en ops). ~180 líneas. | `engine/core/vn_scene_fx.c` |
| Paso 4 — VM host (notify + run_vm) | Mover `notify` (L360-465) y `run_vm` (L1145-1202) usando las ops de audio, `get_frame_count`, `res_*` por ops. ~170 líneas. | `engine/core/vn_vm_host.c` |
| Paso 5 — Entrada y menús | Mover `update_dev`, `list_input`, `update_title`, `update_pause_menu`, `update_slots`, `update_confirm`, `update_options`, `update_gallery`, `update_extras`, `update_menu`, `update_imgmenu`, `update_say`, `autoplay_step`, `skip_step`. ~420 líneas: dividir en dos pasos (5a menús, 5b diálogo/salto). | `engine/core/vn_menus.c` |
| Paso 6 — Render de escena y caja | Mover `scene_sync`, `draw_bg`, `draw_solid`, `draw_scene`, `draw_box`, `draw_menu`, `draw_imgmenu`, `draw_dev`, `draw_debug`. ~360 líneas. | `engine/core/vn_render.c` |
| Paso 7 — Guardado y slots | Mover `show_now`, `card_error`, `write_card`, `save_slot`, `load_slot`, `do_save`, `go_title` (parte de guardado). ~120 líneas. | `engine/core/vn_save_ui.c` |
| Paso 8 — Bucle principal y bootstrap | Mantener `main()` en un punto de entrada por plataforma (`platforms/ps1/main_ps1.c`) que inicializa hardware y llama a `vn_app_run(ops)`; mover el bucle `for(;;)` (L2190-2370) al núcleo usando ops. ~180 líneas de bucle + bootstrap mínimo. | `engine/core/vn_app.c + platforms/ps1/main_ps1.c` |

Estimación total movida: ~1800 líneas de las 2371 de `main.c` (el resto son bootstrap de hardware, que se queda en el backend).
## 9. Dudas y puntos no claros
- `video_frames()` (12 usos) se usa como base de tiempo (cámara, transiciones, caja, FPS). ¿Es el contador de VSync de la GPU o un contador del módulo `video`? En PS1 ambos coinciden, pero en otras plataformas puede no existir; conviene definir `get_frame_count()` y su frecuencia en `VnPlatformOps`. Archivo: `main.c:383, 386, 608, 628, 950, 1016, 1151, 1674, 1861?` (ver tabla).
- `cd_sync_vblanks` y `cd_wait_vblanks` son variables globales del módulo `cd` (leídas en `main.c:1159, 1162`). Si `main.c` se mueve al núcleo, no puede tocarlas; hace falta una op (`get_cd_vblank_counts`) o mover el cálculo de `decode_vblanks` al módulo `cd`.
- `res_trace_tag` es una variable global de `res` (asignada en `main.c:1150`). Misma situación: op `res_set_trace_tag()` o encapsular en `res`.
- `decode_vblanks` (L482) es un contador propio de `main.c` usado para medir decodificación; es portable y puede quedarse en el núcleo.
- `img_brightness` se asigna directamente en el bucle principal (`main.c:2294, 2297`) y se lee en `img_draw_ex`. Es estado global del módulo `img`; para portabilidad conviene una op `set_image_brightness()` o pasarla como parámetro.
- `text_string()` (L309-320) resuelve cadenas de texto localizadas del capítulo; depende de `chapter` y `text` del núcleo ya portados. Portable, pero usa `vm` global. Al mover, pasar el contexto.
- `fatal()` (L126-137) imprime y dibuja con `printf`/`video_*`/`VSync`; es de bootstrap y debería quedarse en el backend o convertirse en `log` + `present`.
- `fmv.c` usa directamente `psx*` (DMA, MDEC, CD) y `res_borrow_cache`; es el módulo menos portable. Se propone mantenerlo como módulo de plataforma y exponer solo `special_fmv` (begin/update/draw) al núcleo mediante la tabla `game_specials`.
- La clasificación asume que `text`, `scene`, `vm`, `chapter` ya son núcleo. Si alguna función de esos módulos en `vn-engine-ps1` sigue usando hardware, la clasificación de las funciones que las llaman podría cambiar.
## 10. Referencias
- `E:\Dev\vn-engine-ps1\app\main.c` (2371 líneas), `app\app.h`, `app\game.h`, `app\ui_text.h`.
- `E:\Dev\vn-engine-ps1\modules\{canvas,credits,fmv,keyboard,phone,strips}.c`, `modules\special.h`.
- `engine\core\vn_platform.h` (contrato C2), `docs\core-api.md`, `PLAN.md` §§3-4, 6.
