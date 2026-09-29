# -*- coding: utf-8 -*-

"""
CONNECTIONS:

- CALLED BY: interface/client_gui.py

Provides a small standalone color selection window.
"""

import customtkinter as ctk


class ColorPicker(ctk.CTkToplevel):

    # LED-enhanced C64-inspired base palette.
    C64_COLORS = [
        "#000000",  # Black
        "#FFFFFF",  # White
        "#C83C3C",  # Red
        "#62DCE8",  # Cyan
        "#9B4DCC",  # Purple
        "#55B84A",  # Green
        "#4141C4",  # Blue
        "#E8D84A",  # Yellow
        "#E87832",  # Orange
        "#8A5A32",  # Brown
        "#E86A6A",  # Light red
        "#4A4A4A",  # Dark gray
        "#7A7A7A",  # Gray
        "#8FDD72",  # Light green
        "#7777E0",  # Light blue
        "#B8B8B8",  # Light gray
    ]

    # Brighter LED-era variants of the C64 palette.
    C64_VARIANTS = [
        "#202020",  # Black variant
        "#F4F4F4",  # White variant
        "#F05252",  # Red variant
        "#82F2FA",  # Cyan variant
        "#C56BE8",  # Purple variant
        "#72D65D",  # Green variant
        "#5C5CE8",  # Blue variant
        "#F5E95A",  # Yellow variant
        "#F58B45",  # Orange variant
        "#A87548",  # Brown variant
        "#F58A8A",  # Light red variant
        "#5C5C5C",  # Dark gray variant
        "#929292",  # Gray variant
        "#AEF08F",  # Light green variant
        "#9292F5",  # Light blue variant
        "#D0D0D0",  # Light gray variant
    ]

    def __init__(
        self,
        parent,
        current_color="#FFFFFF",
        callback=None,
    ):
        super().__init__(parent)

        self.parent_window = parent
        self.current_color = str(
            current_color
        ).strip().upper()
        self.callback = callback

        self.title("Text Color")
        self.resizable(False, False)
        self.transient(parent)

        self.configure(
            fg_color="#10172A"
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.destroy,
        )

        self._build_ui()

        self.update_idletasks()
        self._center_on_parent()

        self.focus_force()

    def _build_ui(self):
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color="#10172A",
        )

        self.main_frame.pack(
            padx=10,
            pady=10,
        )

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Text Color",
            font=("Arial", 12, "bold"),
        )

        self.title_label.grid(
            row=0,
            column=0,
            columnspan=8,
            padx=5,
            pady=(0, 8),
        )

        colors = (
            self.C64_COLORS
            + self.C64_VARIANTS
        )

        for index, color in enumerate(colors):

            row = 1 + (index // 8)
            column = index % 8

            button = ctk.CTkButton(
                self.main_frame,
                text="",
                width=28,
                height=28,
                corner_radius=4,
                fg_color=color,
                hover_color=color,
                border_width=2
                if color.upper() == self.current_color
                else 0,
                border_color="#FFFFFF",
                command=lambda selected=color:
                    self._select_color(selected),
            )

            button.grid(
                row=row,
                column=column,
                padx=3,
                pady=3,
            )

    def _select_color(self, color):
        selected_color = str(
            color
        ).strip().upper()

        if self.callback:
            self.callback(
                selected_color
            )

        self.destroy()

    def _center_on_parent(self):
        self.update_idletasks()

        parent_x = self.parent_window.winfo_rootx()
        parent_y = self.parent_window.winfo_rooty()

        parent_width = self.parent_window.winfo_width()
        parent_height = self.parent_window.winfo_height()

        window_width = self.winfo_width()
        window_height = self.winfo_height()

        x = (
            parent_x
            + (parent_width - window_width) // 2
        )

        y = (
            parent_y
            + (parent_height - window_height) // 2
        )

        self.geometry(
            f"{window_width}x"
            f"{window_height}+{x}+{y}"
        )