# -*- coding: utf-8 -*-
"""
KOPPLINGAR:
- HÄMTAR FRÅN: Isolerade UI-händelser (Inga interna importberoenden mot presentation).
- ANROPAS AV: interface/client_gui.py
"""

import json
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

        if gui_instance.core_hub and hasattr(
            gui_instance.core_hub,
            "start_ai_runtime"
        ):
            gui_instance.core_hub.start_ai_runtime()

    else:
        log_text = (
            gui_instance.localizer.get_text("log_ai_off")
            if gui_instance.localizer
            else "AI OFF"
        )
        gui_instance.append_log("SYSTEM", log_text)

        if gui_instance.core_hub and hasattr(
            gui_instance.core_hub,
            "stop_ai_runtime"
        ):
            gui_instance.core_hub.stop_ai_runtime()

    function_sync_matrix_to_core(gui_instance)


def function_on_internet_toggle(gui_instance):
    """Handles the transactional state swap for the Internet AI capability block."""
    function_sync_matrix_to_core(gui_instance)


def function_sync_matrix_to_core(gui_instance):
    """Synchronizes GUI switch states with RuntimeStateCore and legacy ChannelMatrix."""

    ch1 = True if gui_instance.chat_switch.get() == 1 else False
    ch2 = True if gui_instance.write_adapter_switch.get() == 1 else False
    ai_active = True if gui_instance.ai_toggle_switch.get() == 1 else False
    ai_channel1 = True if gui_instance.ai_chat_switch.get() == 1 else False
    ai_voice = True if gui_instance.voice_ai_switch.get() == 1 else False
    user_voice = True if gui_instance.voice_user_switch.get() == 1 else False
    internet_active = True if gui_instance.internet_toggle.get() == 1 else False
    telemetry_active = True if gui_instance.read_telemetry_switch.get() == 1 else False

    # ---------------------------------------------------------
    # RUNTIME STATE — current ACL/state model
    # ---------------------------------------------------------
    if hasattr(gui_instance, "runtime_state") and gui_instance.runtime_state:
        gui_instance.runtime_state.set_state(
            "channel1_active",
            ch1
        )

        gui_instance.runtime_state.set_state(
            "ai_channel1_active",
            ai_channel1
        )

        gui_instance.runtime_state.set_state(
            "ai_voice_active",
            ai_voice
        )

        gui_instance.runtime_state.set_state(
            "user_voice_active",
            user_voice
        )

        gui_instance.runtime_state.set_state(
            "channel2_active",
            ch2
        )

        gui_instance.runtime_state.set_state(
            "ai_active",
            ai_active
        )

        gui_instance.runtime_state.set_state(
            "telemetry_active",
            telemetry_active
        )

    # ---------------------------------------------------------
    # LEGACY MATRIX — retained for existing backend compatibility
    # ---------------------------------------------------------
    if not gui_instance.matrix:
        return

    gui_instance.matrix.update_states(
        ch1_chat=ch1,
        ch2_adapter=ch2,
        ai_active=ai_active,
        internet_active=internet_active,
    )


def function_on_telemetry_toggle(gui_instance):
    """
    Controls the already-existing TelemetryCore worker through
    pause/resume state transitions.

    Worker creation and thread lifecycle belong exclusively to main.py.
    The GUI switch is therefore a soft-reset control and must never
    create another polling worker.
    """
    if (
        not gui_instance.core_hub
        or not hasattr(gui_instance.core_hub, "telemetry_worker")
    ):
        return

    worker = gui_instance.core_hub.telemetry_worker

    if gui_instance.read_telemetry_switch.get() == 1:
        # Telemetry worker is created and started exactly once by main.py.
        # GUI only releases the existing worker from its paused state.
        worker.resume()

        log_text = (
            gui_instance.localizer.get_text("log_tel_on")
            if gui_instance.localizer
            else "Telemetry ON"
        )
        gui_instance.append_log("I/O-SIGNAL", log_text)

    else:
        # Soft pause only.
        # The worker thread remains alive and is resumed by the next ON event.
        worker.pause()

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

        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = False

    else:
        gui_instance.entry_field.configure(state="normal")
        gui_instance.send_button.configure(state="normal")
        gui_instance.append_log("SYSTEM", "Keyboard focus released.")

        if gui_instance.core_hub and hasattr(gui_instance.core_hub, "hardware"):
            gui_instance.core_hub.hardware.is_listening = True


def function_on_model_change(gui_instance, selected_model):
    """Registers the modified cognitive targets inside global serialization tables on disk."""
    gui_instance.append_log("SYSTEM", f"Model changed to: {selected_model}")

    if gui_instance.core_hub and hasattr(gui_instance.core_hub, "ai_client"):
        if gui_instance.core_hub.ai_client is not None:
            gui_instance.core_hub.ai_client.model_name = selected_model

        gui_instance.core_hub.global_config["ai_model_name"] = selected_model

        try:
            with open(
                gui_instance.core_hub.config_path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    gui_instance.core_hub.global_config,
                    f,
                    indent=4
                )

        except Exception as e:
            print(
                f"[GUI-FUNCTION-ERROR] "
                f"Failed to persist master config: {e}"
            )


def function_on_adapter_change(gui_instance, selected_adapter):
    """Swaps dynamic pipeline references within central context containers cleanly."""
    no_adapter_text = (
        gui_instance.localizer.get_text("no_adapter")
        if gui_instance.localizer
        else "No Adapter Loaded"
    )

    if selected_adapter == no_adapter_text:
        gui_instance.boot_target_btn.configure(state="disabled")

        # Channel 2 must always be OFF and locked without an active adapter.
        gui_instance.write_adapter_switch.deselect()
        gui_instance.write_adapter_switch.configure(
            state="disabled"
        )

        # Telemetry must always be OFF and locked without an active adapter.
        gui_instance.read_telemetry_switch.deselect()
        gui_instance.read_telemetry_switch.configure(
            state="disabled"
        )

        gui_instance.append_log("SYSTEM", "Adapter detached.")

        if gui_instance.core_hub:
            gui_instance.core_hub.unload_active_adapter()

    else:
        gui_instance.boot_target_btn.configure(state="normal")

        gui_instance.append_log(
            "SYSTEM",
            f"Adapter attached: {selected_adapter}"
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


def function_open_external_link(url):
    """Receives a URL directly from ChatWindow and opens it externally."""
    if not url:
        return

    try:
        function_open_browser_link(str(url))
    except Exception as e:
        print(
            "[GUI-FUNCTION-ERROR] "
            f"External link handling failed: {e}"
        )