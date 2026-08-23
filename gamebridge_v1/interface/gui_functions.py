# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: Isolerade UI-händelser (Inga interna importberoenden mot presentation).
- ANROPAS AV: interface/client_gui.py
"""
import json
import os
import re
import threading
from functions.internet_functions import function_open_browser_link


def function_on_ai_toggle(gui_instance):
    """Dispatches dynamic tracking logs for the main AI engine switch."""
    if gui_instance.ai_toggle_switch.get() == 1:
        log_text = (
            gui_instance.localizer.get_text("log_ai_on")
            if gui_instance.localizer
            else "AI ON"
        )
        gui_instance.append_log("SYSTEM", log_text)
    else:
        log_text = (
            gui_instance.localizer.get_text("log_ai_off")
            if gui_instance.localizer
            else "AI OFF"
        )
        gui_instance.append_log("SYSTEM", log_text)
    function_sync_matrix_to_core(gui_instance)


def function_on_internet_toggle(gui_instance):
    """Handles the transactional state swap for the Internet AI capability block."""
    function_sync_matrix_to_core(gui_instance)


def function_sync_matrix_to_core(gui_instance):
    """Transactionally pushes localized switch values directly into the core matrix module."""
    if not gui_instance.matrix:
        return

    ch1 = True if gui_instance.chat_switch.get() == 1 else False
    ch2 = True if gui_instance.write_adapter_switch.get() == 1 else False
    ai_active = True if gui_instance.ai_toggle_switch.get() == 1 else False
    internet_active = True if gui_instance.internet_toggle.get() == 1 else False

    # INTEGRATION: Skicka det fjärde argumentet till ChannelMatrix för atomisk nätverksspärr
    gui_instance.matrix.update_states(
        ch1_chat=ch1,
        ch2_adapter=ch2,
        ai_active=ai_active,
        internet_active=internet_active,
    )

    if gui_instance.core_hub:
        gui_instance.core_hub.set_channels_state(ch1, ch2)


def function_on_telemetry_toggle(gui_instance):
    """Triggers the decoupled TelemetryCore worker loop based on widget state context and forces matrix sync."""
    if (
        not gui_instance.core_hub
        or not hasattr(gui_instance.core_hub, "telemetry_worker")
    ):
        return

    worker = gui_instance.core_hub.telemetry_worker

    if gui_instance.read_telemetry_switch.get() == 1:
        # Systemisk injektion: Om arbetartråden aldrig startats, plugga in våra callbacks nu
        if not worker.loop_active:

            def get_active_adapter():
                return getattr(gui_instance.core_hub, "active_adapter_instance", None)

            def telemetry_success_callback(data):
                if hasattr(gui_instance, "chat_window"):
                    gui_instance.chat_window.append_monitor_message(str(data))

            worker.start_polling_worker(
                current_adapter_callback=get_active_adapter,
                success_ui_callback=telemetry_success_callback,
            )

        worker.set_loop_state(True)
        log_text = (
            gui_instance.localizer.get_text("log_tel_on")
            if gui_instance.localizer
            else "Telemetry ON"
        )
        gui_instance.append_log("I/O-SIGNAL", log_text)
    else:
        worker.set_loop_state(False)
        log_text = (
            gui_instance.localizer.get_text("log_tel_off")
            if gui_instance.localizer
            else "Telemetry OFF"
        )
        gui_instance.append_log("I/O-SIGNAL", log_text)

    function_sync_matrix_to_core(gui_instance)


def function_on_lock_toggle(gui_instance):
    """Enforces safe keyboard barriers protecting peripheral data allocations inside HardwareIO."""
    if gui_instance.lock_switch.get() == 1:
        gui_instance.entry_field.configure(state="disabled")
        gui_instance.send_button.configure(state="disabled")
        gui_instance.append_log("SYSTEM", "Keyboard focus locked.")
        # INTEGRATION: Sätter flaggan i HardwareIO så att systemet vet att fysiska avbrott är spärrade
        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = False
    else:
        gui_instance.entry_field.configure(state="normal")
        gui_instance.send_button.configure(state="normal")
        gui_instance.append_log("SYSTEM", "Keyboard focus released.")
        # INTEGRATION: Återställer flaggan i HardwareIO till operationell status
        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = True


def function_on_model_change(gui_instance, selected_model):
    """Registers the modified cognitive targets inside global serialization tables on disk."""
    gui_instance.append_log("SYSTEM", f"Model changed to: {selected_model}")
    if gui_instance.core_hub and hasattr(gui_instance.core_hub, "ai_client"):
        gui_instance.core_hub.ai_client.model_name = selected_model
        gui_instance.core_hub.global_config["ai_model_name"] = selected_model
        try:
            with open(
                gui_instance.core_hub.config_path, "w", encoding="utf-8"
            ) as f:
                json.dump(
                    gui_instance.core_hub.global_config, f, indent=4
                )
        except Exception as e:
            print(f"[GUI-FUNCTION-ERROR] Failed to persist master config: {e}")


def function_on_adapter_change(gui_instance, selected_adapter):
    """Swaps dynamic pipeline references within central context containers cleanly."""
    no_adapter_text = (
        gui_instance.localizer.get_text("no_adapter")
        if gui_instance.localizer
        else "No Adapter Loaded"
    )
    if selected_adapter == no_adapter_text:
        gui_instance.boot_target_btn.configure(state="disabled")
        gui_instance.append_log("SYSTEM", "Adapter detached.")
        if gui_instance.core_hub:
            gui_instance.core_hub.unload_active_adapter()
    else:
        gui_instance.boot_target_btn.configure(state="normal")
        gui_instance.append_log(
            "SYSTEM", f"Adapter attached: {selected_adapter}"
        )
        if gui_instance.core_hub:
            gui_instance.core_hub.handle_adapter_switch(selected_adapter)


def function_trigger_text_input(gui_instance):
    """Relays local text streams to underlying cognitive pipelines asynchronously."""
    if gui_instance.lock_switch.get() == 1:
        return
    text = gui_instance.entry_field.get().strip()
    if not text:
        return
    gui_instance.entry_field.delete(0, "end")

    sender_tag = (
        "USER (Channel 1)"
        if gui_instance.chat_switch.get() == 1
        else "USER (Raw Stream)"
    )
    gui_instance.append_log(sender_tag, text)

    if gui_instance.core_hub:
        threading.Thread(
            target=gui_instance.core_hub.process_chatt_flow,
            args=(text,),
            daemon=True,
        ).start()


def function_handle_log_double_click(gui_instance, event):
    """Parses the current line under the mouse cursor to extract and open tagged URLs."""
    try:
        # Hämta exakt index för tecknet under muspekaren vid klicket
        click_index = gui_instance.log_box.index(f"@{event.x},{event.y}")

        # Kontrollera om tecknet har taggen "hyperlink" på sig
        tags = gui_instance.log_box.tag_names(click_index)

        if "hyperlink" in tags:
            # Hitta radnumret
            line_num = click_index.split(".")[0]

            # Hämta hela textraden
            full_line = gui_instance.log_box.get(
                f"{line_num}.0", f"{line_num}.end"
            ).strip()

            # Extrahera URL:en med Regex
            url_match = re.search(r"(https?://[^\s\)\}\]\",\']+)", full_line)
            if url_match:
                detected_url = url_match.group(1)
                # Skicka länken asynkront till standardwebbläsaren
                function_open_browser_link(detected_url)
    except Exception as e:
        print(f"[GUI-FUNCTION-ERROR] Link click parsing failed: {e}")
