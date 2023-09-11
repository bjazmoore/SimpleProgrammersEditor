import tkinter as tk
from tkinter import filedialog, simpledialog, ttk, font
import json
import re

class TextWithLineNumbers(tk.Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.light_mode = {
            'bg': '#FFFFFF',
            'fg': '#000000',
            'fg-linenum': '#7C98B4',
            'insertbackground': '#000000'  # cursor color
        }

        self.dark_mode = {
            'bg': '#2E2E2E',
            'fg': '#FFFFFF',
            'fg-linenum': '#C6E4F7',
            'insertbackground': '#FFFFFF'  # cursor color
        }

        # Default values
        self.tab_spaces = 5
        self.is_dark_mode = tk.IntVar(value=0)  # 0 means dark mode is off by default
        self.use_spaces_for_tab = tk.IntVar(value=0)  # By default, this option is off
        self.word_wrap = tk.BooleanVar(value=True)  # default is word wrap ON
        self.show_indentation_var = tk.BooleanVar(value=False) #indentation is OFF
        self.filename = None
        self.default_font_size = 10  # Default font size initialization
        self.sticky_indentation = tk.IntVar(value=1)  # Default: on

        self.my_font = "Courier New"
        if not self.is_font_available(self.my_font):
            self.my_font = "TkDefaultFont"


        # Load configurations
        self.load_configurations()

        # Set the title for your main window
        self.master.title("Simple Programmers Editor")

        # Line Numbers (left side)
        self.line_numbers = tk.Text(self, width=4)
        self.line_numbers.grid(row=0, column=0, rowspan=2, sticky="ns")

        # Main Text Editor
        self.text = tk.Text(self, wrap=tk.WORD)
        self.text.grid(row=0, column=1, sticky="nsew")

        # Vertical Scrollbar (right side)
        self.scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self._yview_both)
        self.text.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.grid(row=0, column=2, sticky="ns")

        # Horizontal Scrollbar
        self.h_scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.config(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.grid(row=1, column=1, sticky="ew")
        self.h_scrollbar.grid_remove()  # Initially, hide it as word wrap is ON

        # Status Bar
        self.status_bar = tk.Frame(self)
        self.status_label_left = tk.Label(self.status_bar, anchor="w")
        self.status_label_right = tk.Label(self.status_bar, anchor="e")

        self.status_label_left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.status_label_right.pack(side=tk.RIGHT)
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky="ew")

        self.update_status_bar()  # Initialize with default values
        self.apply_font_attributes() #apply the font attributes set in defaults



        #bindings ------------------------------------------
        self.text.bind('<KeyRelease>', self._key_release)
        self.text.bind("<<Modified>>", self._modified)
        self.text.bind('<ButtonRelease-1>', self._button_release_1)
        self.text.bind('<MouseWheel>', self._on_text_scroll)
        self.text.bind('<Button-4>', self._on_text_scroll)  # For Linux, bind button-4 and button-5 to handle mouse scrolling
        self.text.bind('<Button-5>', self._on_text_scroll)
        self.line_numbers.bind("<FocusIn>", self._redirect_focus)
        self.text.bind('<Tab>', self.handle_tab)
        self.text.bind('<Return>', self.handle_enter)
        self.text.bind('<Configure>', self.sync_line_numbers_view)

        self.new_file()
        self.toggle_dark_mode()

        # Adjusting row and column weights for resizing behavior
        self.grid_rowconfigure(0, weight=1)  # main row containing text widget and vertical scrollbar
        self.grid_columnconfigure(1, weight=1)  # main column containing the main text widget


    #Functions for bindings --------------------------------
    def _key_release(self, event=None):
        self._update_line_numbers()
        self.update_status_bar()
        self.sync_line_numbers_view()
        if self.show_indentation_var.get():
            self.display_indentation()

    def _modified(self, event=None):
        self._on_text_modified()

    def _button_release_1(self, event=None):
        self.update_status_bar()
        self.remove_highlight()

    def _redirect_focus(self, event):
        self.text.focus_set()


    #Menus ----------------------------------------------------
    def create_menus(self):
        # Add the menu bar to the root window
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # Create the File menu with its items
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="New", command=self.new_file)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Save As...", command=self.save_file_as)
        self.file_menu.add_command(label="Close", command=self.close_file)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_editor)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Create the Edit menu with its items
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Copy", command=self.copy_text)
        self.edit_menu.add_command(label="Cut", command=self.cut_text)
        self.edit_menu.add_command(label="Paste", command=self.paste_text)
        self.edit_menu.add_separator()  # Add a separator
        self.edit_menu.add_command(label="Find", command=self.open_search_dialog)
        self.edit_menu.add_command(label="Find/Replace", command=self.open_replace_dialog)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)

        # Create the 'Options' menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Font Size", command=self.open_font_size_dialog)
        self.options_menu.add_command(label="Font Family", command=self.show_font_family_dialog)
        self.options_menu.add_separator()  # Add a separator
        self.options_menu.add_checkbutton(label="Toggle Word Wrap", onvalue=True, offvalue=False, variable=self.word_wrap, command=self.toggle_word_wrap)
        self.options_menu.add_checkbutton(label="Dark Mode", variable=self.is_dark_mode, command=self.toggle_dark_mode)
        self.options_menu.add_separator()  # Add a separator
        self.options_menu.add_checkbutton(label="Spaces for Tab", variable=self.use_spaces_for_tab)
        self.options_menu.add_checkbutton(label="Sticky Indentation", variable=self.sticky_indentation)
        self.options_menu.add_checkbutton(label="Show Indentation", variable=self.show_indentation_var, command=self.toggle_indentation_display)
        self.options_menu.add_separator()  # Add a separator
        self.options_menu.add_command(label="Settings", command=self.open_settings)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)


    # File System Funtions ------------------------------------------------------------------------------
    def new_file(self):
        if self.text.edit_modified():
            save_changes = tk.messagebox.askyesnocancel("Save changes?", "Do you want to save changes?")
            if save_changes is None:
                return
            if save_changes:
                self.save_file()
        self.text.delete(1.0, tk.END)
        self.text.mark_set(tk.INSERT, "1.0")  # Set the cursor to line 1, column 1 after loading the file
        self.text.focus_set()  # Set focus to the text widget
        self.filename = None
        self.show_indentation_var.set(False)
        self._update_line_numbers()  # Refresh line numbers
        self.update_status_bar()


    def open_file(self):
        filepath = filedialog.askopenfilename()
        if not filepath:
            return
        self.text.delete(1.0, tk.END)
        with open(filepath, "r") as file:
            self.text.insert(1.0, file.read())
        self.text.mark_set(tk.INSERT, "1.0")  # Set the cursor to line 1, column 1 after loading the file
        self.text.focus_set()  # Set focus to the text widget
        self.filename = filepath
        self.show_indentation_var.set(False)
        self._update_line_numbers()  # Refresh line numbers
        self.update_status_bar()


    def save_file(self):
        if self.filename:
            if self.show_indentation_var.get():
                #indentation is enabled - disable it
                self.hide_indentation()
            with open(self.filename, "w") as file:
                file.write(self.text.get(1.0, tk.END))
                self.text.edit_modified(False)
                self._on_text_modified()
            if self.show_indentation_var.get():
                #indentation is still enabled - display it again
                self.display_indentation()
        else:
            self.save_file_as()


    def save_file_as(self):
        filepath = filedialog.asksaveasfilename()
        if not filepath:
            return
        if self.show_indentation_var.get():
            #indentation is enabled - disable it
            self.hide_indentation()
        with open(filepath, "w") as file:
            file.write(self.text.get(1.0, tk.END))
        self.filename = filepath
        self.text.edit_modified(False)
        self._on_text_modified()
        if self.show_indentation_var.get():
            #indentation is still enabled - display it again
            self.display_indentation()
        self.update_status_bar()


    def close_file(self):
        if self.text.edit_modified():
            save_changes = tk.messagebox.askyesnocancel("Save changes?", "Do you want to save changes?")
            if save_changes is None:
                return
            if save_changes:
                self.save_file()
        self.text.delete(1.0, tk.END)
        self.filename = None
        self._update_line_numbers()  # Refresh line numbers
        self.text.edit_modified(False)
        self.show_indentation_var.set(False)
        self._on_text_modified()


    def exit_editor(self):
        if self.text.edit_modified():
            answer = tk.messagebox.askyesnocancel("Save Changes", "Do you want to save changes before exiting?")
            if answer:
                self.save_file()
            elif answer is None:  # Cancel was selected
                return
        root.destroy()


    # Cut / Copy / Paste functions ---------------------------------------
    def copy_text(self):
        """Copy the currently selected text to the clipboard."""
        try:
            selected_text = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_clear()
            self.master.clipboard_append(selected_text)
        except tk.TclError:
            pass  # No text selected

    def cut_text(self):
        """Cut the currently selected text and place it in the clipboard."""
        try:
            selected_text = self.text.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.master.clipboard_clear()
            self.master.clipboard_append(selected_text)
            self.text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass  # No text selected

    def paste_text(self):
        """Paste the text currently in the clipboard."""
        try:
            clipboard_text = self.master.clipboard_get()
            self.text.insert(tk.INSERT, clipboard_text)
        except tk.TclError:
            pass  # No text in clipboard or some other error


    #Handle Scrolling -------------------------------------------------
    def _on_text_scroll(self, event):
        # Calculate the scroll amount
        scroll_amount = -1*(event.delta//120)

        # Scroll both text widget and line numbers
        self.line_numbers.yview("scroll", scroll_amount, "units")
        self.text.yview("scroll", scroll_amount, "units")

        # Get the line number of the first visible line in the Text widget
        top_line = int(self.text.index("@0,0").split('.')[0])

        # Set the cursor position to the first visible line
        self.text.mark_set(tk.INSERT, f"{top_line}.0")
        self.update_status_bar()

        return "break"  # To prevent default behavior


    def _yview_both(self, *args):
        # Synchronize yview for both main text and line numbers text
        self.text.yview(*args)
        self.line_numbers.yview(*args)


    #Manage sticky indentation ---------------------------------------
    def handle_enter(self, event):
        if self.sticky_indentation.get():
            # Get the current line number
            line, _ = self.text.index(tk.INSERT).split('.')
            # Get the content of the current line before the insertion point
            current_line_content = self.text.get(f"{line}.0", tk.INSERT)
            # Find the white spaces (tabs or spaces) at the beginning of the line
            indentation = ""
            for char in current_line_content:
                if char in (" ", "\t", "¦"):
                    indentation += char
                else:
                    break
            # Insert the same indentation to the new line after the insertion point
            self.text.insert(tk.INSERT, "\n" + indentation)
            return "break"  # This prevents the default behavior
        return None  # This allows the normal Enter behavior if the option is not checked


    #indentation display ----------------------------------------
    def toggle_indentation_display(self):
        if self.show_indentation_var.get():
            self.display_indentation()
        else:
            self.hide_indentation()


    def display_indentation(self):
        cursor_position = self.text.index(tk.INSERT)  # Save cursor position
        top_line = int(self.text.index("@0,0").split('.')[0])
        self.original_content = self.text.get("1.0", "end-1c")

        # Replace every 'self.tab_spaces' spaces with '    ·'
        replacement = ' '*(self.tab_spaces-1)
        replacement += '¦'
        indent_space_pattern = re.compile(' ' * self.tab_spaces)
        content_with_indentation = indent_space_pattern.sub(replacement, self.original_content)

        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content_with_indentation)
        self._update_line_numbers()  # Refresh line numbers

        # Scroll until the original cursor position comes into view
        self.text.mark_set(tk.INSERT, cursor_position)  # Restore cursor position temporarily for the loop
        while top_line != int(self.text.index("@0,0").split('.')[0]):  # While cursor is not visible, keep scrolling
            self.text.yview_scroll(1, tk.UNITS)
            self.line_numbers.yview_scroll(1, tk.UNITS)



    def hide_indentation(self, event=None):
        # Save the current cursor position
        cursor_position = self.text.index(tk.INSERT)
        top_line = int(self.text.index("@0,0").split('.')[0])

        # Get the current content and replace the indentation markers
        content = self.text.get(1.0, tk.END)
        updated_content = content.replace("¦", " ")

        # Update the content in the text widget
        self.text.delete(1.0, tk.END)
        self.text.insert(1.0, updated_content[:-1])
        self._update_line_numbers()  # Refresh line numbers

        # Scroll until the original cursor position comes into view
        self.text.mark_set(tk.INSERT, cursor_position)  # Restore cursor position temporarily for the loop
        while top_line != int(self.text.index("@0,0").split('.')[0]):  # While cursor is not visible, keep scrolling
            self.text.yview_scroll(1, tk.UNITS)
            self.line_numbers.yview_scroll(1, tk.UNITS)



    def sync_line_numbers_view(self, event=None):
        # Synchronize the line numbers view with the text widget
        top_fraction, _ = self.text.yview()
        self.line_numbers.yview_moveto(top_fraction)


    #Manage Wordwrap --------------------------------------------------
    def toggle_word_wrap(self):
        if self.word_wrap.get():
            #prepare to return to this view - get cursor position and top line.
            cursor_position = self.text.index(tk.INSERT)  # Save cursor position
            top_line = int(self.text.index("@0,0").split('.')[0])
            #Enable Wordwrap at the word
            self.text.config(wrap=tk.WORD)  # Change to tk.CHAR if you prefer to wrap at character
            self.h_scrollbar.grid_remove()  # Hide the horizontal scrollbar
            self.text.mark_set(tk.INSERT, 1.0)
            self._update_line_numbers()
            #Now reposition the view
            self.text.mark_set(tk.INSERT, cursor_position)  # Restore cursor position temporarily for the loop
            while top_line != int(self.text.index("@0,0").split('.')[0]):  # While cursor is not visible, keep scrolling
                self.text.yview_scroll(1, tk.UNITS)
                self.line_numbers.yview_scroll(1, tk.UNITS)
        else:
            #prepare to return to this view - get cursor position and top line.
            cursor_position = self.text.index(tk.INSERT)  # Save cursor position
            top_line = int(self.text.index("@0,0").split('.')[0])
            #Disable Wordwrap
            self.text.config(wrap=tk.NONE)
            self.h_scrollbar.grid()  # Show the horizontal scrollbar
            self.text.grid_rowconfigure(1, weight=1)  # Ensure the scrollbar occupies its space fully
            self.text.mark_set(tk.INSERT, 1.0)
            self._update_line_numbers()
            #Now reposition the view
            self.text.mark_set(tk.INSERT, cursor_position)  # Restore cursor position temporarily for the loop
            while top_line != int(self.text.index("@0,0").split('.')[0]):  # While cursor is not visible, keep scrolling
                self.text.yview_scroll(1, tk.UNITS)
                self.line_numbers.yview_scroll(1, tk.UNITS)


    #Other functions --------------------------------------------------
    def apply_font_attributes(self):
        self.text.config(font=(self.my_font, self.default_font_size))
        self.line_numbers.config(font=(self.my_font, self.default_font_size))


    #validate that a string is a valid color hex code
    def is_valid_hex_color(self, color):
        pattern = r'^#?([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return re.match(pattern, color) is not None


    def open_settings(self, event=None):
        settings_dialog = self.open_main_frame()
        self.wait_window(settings_dialog)  # This makes the dialog modal; remove if you don't want that behavior.


    def is_font_available(self, font_name):
        available_fonts = font.families()
        return font_name in available_fonts


    #remove all highlighted text from last search
    def remove_highlight(self, event=None):
        self.text.tag_remove("search", 1.0, tk.END)


    # Update the status bar
    def update_status_bar(self):
        # Display filename or "Unnamed" on the left side
        filename_display = "Filename: "
        filename_display += self.filename if self.filename else "Unnamed"
        self.status_label_left.config(text=filename_display)

        # Display line and column number on the right side
        line, col = self.text.index(tk.INSERT).split('.')
        self.status_label_right.config(text=f"Line: {line} | Col: {col}")


    def handle_tab(self, event):
        if self.use_spaces_for_tab.get():
            self.text.insert(tk.INSERT, ' ' * self.tab_spaces)
            return "break"  # This prevents the default behavior
        return None  # This allows the normal Tab behavior if the option is not checked


    def toggle_dark_mode(self):
        if self.is_dark_mode.get():
            mode_colors = self.dark_mode
        else:
            mode_colors = self.light_mode

        # Update main text widget
        self.text.config(
            bg=mode_colors['bg'],
            fg=mode_colors['fg'],
            insertbackground=mode_colors['insertbackground']
        )

        # Update line numbers widget
        self.line_numbers.config(
            bg=mode_colors['bg'],
            fg=mode_colors['fg-linenum']
        )

        # Update status bar
        self.status_bar.config(
            bg=mode_colors['bg']
        )

        # Update status labels
        self.status_label_left.config(
            bg=mode_colors['bg'],
            fg=mode_colors['fg-linenum']
        )

        self.status_label_right.config(
            bg=mode_colors['bg'],
            fg=mode_colors['fg-linenum']
        )


    def _on_text_modified(self):
        title = "Simple Programming Editor"
        if self.text.edit_modified():
            title += " •"
        self.master.title(title)


    def _update_line_numbers(self):
        lines = int(self.text.index("end-1c").split('.')[0])  # Get the total number of lines
        line_numbers = []
        for i in range(1, lines + 1):
            wraps = self.inspect_wrapline_at(i)
            if wraps == 1:  # If there's no wrap, just append the line number
                line_numbers.append(str(i))
            else:  # If there's wrapping, append the line number once, and blanks for the remaining wrapped lines
                line_numbers.append(str(i))
                line_numbers.extend([''] * (wraps - 1))
        line_nums = '\n'.join(line_numbers)

        self.line_numbers.configure(state=tk.NORMAL)
        self.line_numbers.config(font=(self.my_font, self.default_font_size))
        self.line_numbers.delete(1.0, tk.END)
        self.line_numbers.insert(1.0, line_nums)
        self.line_numbers.configure(state=tk.DISABLED)


    def inspect_wrapline_at(self, line):
        start = f"{line}.0 linestart"
        end = f"{line}.0 lineend"
        counter = self.text.count(start, end, "displaylines")
        return counter[0] + 1 if counter else 1


    #Font Selection Dialog -------------------------------------------
    def show_font_family_dialog(self):
        # Call FontFamilyDialog to get a possible new font
        new_font_family = self.font_family_dialog(self.my_font)

        # If we got a result back then make the changes...
        if new_font_family:
            self.my_font = new_font_family
            self.apply_font_attributes()



    def font_family_dialog(self, current_font):
        dialog = tk.Toplevel(self)
        dialog.title("Select Font Family")

        self.body(dialog, current_font)

        button = ttk.Button(dialog, text="Apply", command=lambda: self.on_font_apply(dialog))
        button.grid(row=2, column=0, padx=10, pady=10)
        button = ttk.Button(dialog, text="Cancel", command=lambda: dialog.destroy())
        button.grid(row=2, column=1, padx=10, pady=10)

        dialog.wait_window()

        return getattr(self, "_selected_font", current_font)  # Return selected font, or the current one if nothing selected

    def on_font_apply(self, dialog):
        self._selected_font = self.font_combobox.get()  # Store the selected font
        dialog.destroy()

    def body(self, master, current_font):
        tk.Label(master, text="Select Font Family:").grid(row=0, columnspan=2)

        self.font_combobox = ttk.Combobox(master, values=self.get_available_fonts(), state="readonly")
        self.font_combobox.set(current_font)
        self.font_combobox.grid(row=1, columnspan=2, padx=10, pady=5)

    def is_font_available(self, font_name):
        available_fonts = font.families()
        return font_name in available_fonts

    def get_available_fonts(self):
        # list of well known mono-space fonts
        fonts = ['Fixedsys',
                 'Terminal',
                 'Courier',
                 'Consolas',
                 'Courier New',
                 'Lucida Console',
                 'MS Gothic',
                 'Ubuntu Mono',
                 'Cascadia Code',
                 'Cascadia Mono',
                 'Lucida Sans Typewriter',
                 'Julia Mono',
                 'Letter Gothic',
                 'Input',
                 'Hack',
                 'Free Mono',
                 'Fira Code',
                 'Fira Mono',
                 'Droid Sans Mono',
                 'Cousine',
                 'Comic Mono',
                 'Liberation Mono',
                 'Menlo',
                 'Monaco',
                 'Monofur',
                 'Noto Mono',
                 'OCR-A',
                 'OCR A Extended',
                 'OCR-B',
                 'OCR B Extended',
                 'Operator Mono',
                 'Overpass Mono',
                 'PragmataPro',
                 'Prestige Elite',
                 'ProFont',
                 'PT Mono',
                 'Roboto Mono',
                 'SF Mono',
                 'Source Code Pro',
                 'Ubuntu Mono',
                 'DejaVu Sans Mono',
                 'Anonymous Pro',
                 'Dina',
                 ]
        fonts_installed = ['TkDefaultFont']
        for font_name in fonts:
            if self.is_font_available(font_name):  # Returns True if available, False otherwise
                fonts_installed.append(font_name)
        return fonts_installed


    # Font Size Dialog ---------------------------------------------
    def open_font_size_dialog(self):
        font_dialog = tk.Toplevel(self)
        font_dialog.title("Font Size")

        label = tk.Label(font_dialog, text="Select Font Size:")
        label.pack(pady=10, padx=10)

        # Font sizes to choose from
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "24", "32"]

        #current_font_size = tk.StringVar(font_dialog, value=str(self.default_font_size))
        current_font_size = tk.DoubleVar(value=8)
        spinbox = tk.Spinbox(font_dialog, from_=8, to=32, values=font_sizes, wrap=True, textvariable=current_font_size)
        current_font_size.set(self.default_font_size)
        spinbox.pack(pady=5, padx=10)

        # Create a frame for the buttons
        button_frame = tk.Frame(font_dialog)
        button_frame.pack(pady=10)

        def apply_font_size():
            size = spinbox.get()
            self.text.config(font=(self.my_font, size))
            self.line_numbers.config(font=(self.my_font, size))
            self.line_numbers.config(font=(self.my_font, size))
            self.default_font_size = int(size)  # Save the selected size
            font_dialog.destroy()

        apply_button = tk.Button(button_frame, text="Apply", command=apply_font_size)
        apply_button.pack(side=tk.LEFT, padx=10)  # pack on the left side of the frame with padding

        cancel_button = tk.Button(button_frame, text="Cancel", command=font_dialog.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)  # pack next to the apply button with padding



    #Find and Find/Replace ------------------------------------------------------
    def open_replace_dialog(self):
        self.open_search_dialog(replace=True)

    def open_search_dialog(self, replace=False):
        search_window = tk.Toplevel(self)
        search_window.title("Find" if not replace else "Find & Replace")

        search_count = 0
        replace_count = 0

        label = tk.Label(search_window, text="Enter text to search for:")
        label.pack(pady=10, padx=10)

        search_entry = tk.Entry(search_window, width=30)
        search_entry.pack(pady=5, padx=10)
        search_entry.focus_set()

        if replace:
            replace_label = tk.Label(search_window, text="Replace with:")
            replace_label.pack(pady=10, padx=10)

            replace_entry = tk.Entry(search_window, width=30)
            replace_entry.pack(pady=5, padx=10)

        def perform_search():
            nonlocal search_count
            # Remove the previous search highlights
            self.text.tag_remove("search", 1.0, tk.END)

            # Search for the string from the current cursor position to the end of the text
            pos = self.text.search(search_entry.get(), self.text.index(tk.INSERT), stopindex=tk.END)

            # Highlight the found string
            if pos:
                search_count += 1
                length = len(search_entry.get())
                row, col = pos.split('.')
                end = f"{row}.{int(col) + length}"
                self.text.tag_add("search", pos, end)
                self.text.tag_configure("search", background="yellow")
                self.text.mark_set(tk.INSERT, end)
                self.text.see(tk.INSERT)
            else:
                if replace:
                    tk.messagebox.showinfo("Search Result", f"Text not found! Searched {search_count} times. Replaced {replace_count} times.")
                else:
                    tk.messagebox.showinfo("Search Result", f"Text not found! Searched {search_count} times.")

        def perform_replace():
            nonlocal replace_count
            # Check if there's any highlighted text
            try:
                start = self.text.index("search.first")
                end = self.text.index("search.last")
                self.text.delete(start, end)
                self.text.insert(start, replace_entry.get())
                replace_count += 1
            except tk.TclError:  # If nothing is highlighted
                pass

            # Now, perform the search to highlight the next occurrence.
            perform_search()

        button_frame = tk.Frame(search_window)

        search_button = tk.Button(button_frame, text="Search", command=perform_search)
        # Changed packing of the search_button
        search_button.pack(side=tk.LEFT, padx=5)

        if replace:
            replace_button = tk.Button(button_frame, text="Replace", command=perform_replace)
            # Changed packing of the replace_button
            replace_button.pack(side=tk.LEFT, padx=5)

        button_frame.pack(pady=5, padx=10)

        search_entry.bind("<Return>", lambda e: perform_search())


    #Configuration Options Dialog -----------------------------------------------------------
    def open_main_frame(self):
        main_window = tk.Toplevel(self)
        main_window.title("Configuration")

        # Create a main frame inside the Toplevel to hold all the widgets
        main_frame = tk.Frame(main_window, padx=20, pady=20)
        main_frame.pack(padx=10, pady=10)  # This creates padding around the frame itself

        # Word wrap
        tk.Checkbutton(main_frame, text="Word Wrap", variable=self.word_wrap).grid(row=0, column=0, sticky="w")

        # Dark mode
        tk.Checkbutton(main_frame, text="Dark Mode", variable=self.is_dark_mode).grid(row=1, column=0, sticky="w")

        # Spaces for Tab
        tk.Checkbutton(main_frame, text="Use Spaces for Tab", variable=self.use_spaces_for_tab).grid(row=2, column=0, sticky="w")

        # Sticky Indentation
        tk.Checkbutton(main_frame, text="Sticky Indentation", variable=self.sticky_indentation).grid(row=3, column=0, sticky="w")


        # Number of spaces for tab
        num_spaces_for_tab_var = tk.StringVar(value=str(self.tab_spaces))
        tk.Label(main_frame, text="Number of Spaces for Tab:").grid(row=4, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=num_spaces_for_tab_var).grid(row=4, column=1)

        # Colors - Dark Mode
        dark_fg_var = tk.StringVar(value=self.dark_mode['fg'])
        dark_bg_var = tk.StringVar(value=self.dark_mode['bg'])
        dark_ln_fg_var = tk.StringVar(value=self.dark_mode['fg-linenum'])
        dark_cursor_var = tk.StringVar(value=self.dark_mode['insertbackground'])

        #fonts attributes
        font_family = tk.StringVar(value=self.my_font)
        font_size = tk.StringVar(value=self.default_font_size)

        tk.Label(main_frame, text="Foreground (Dark Mode):").grid(row=5, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=dark_fg_var).grid(row=5, column=1)

        tk.Label(main_frame, text="Background (Dark Mode):").grid(row=6, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=dark_bg_var).grid(row=6, column=1)

        tk.Label(main_frame, text="Line Numbers Foreground (Dark Mode):").grid(row=7, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=dark_ln_fg_var).grid(row=7, column=1)

        tk.Label(main_frame, text="Cursor Color (Dark Mode):").grid(row=8, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=dark_cursor_var).grid(row=8, column=1)

        # Colors - Light Mode
        light_fg_var = tk.StringVar(value=self.light_mode['fg'])
        light_bg_var = tk.StringVar(value=self.light_mode['bg'])
        light_ln_fg_var = tk.StringVar(value=self.light_mode['fg-linenum'])
        light_cursor_var = tk.StringVar(value=self.light_mode['insertbackground'])

        tk.Label(main_frame, text="Foreground (Light Mode):").grid(row=9, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=light_fg_var).grid(row=9, column=1)

        tk.Label(main_frame, text="Background (Light Mode):").grid(row=10, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=light_bg_var).grid(row=10, column=1)

        tk.Label(main_frame, text="Line Numbers Foreground (Light Mode):").grid(row=11, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=light_ln_fg_var).grid(row=11, column=1)

        tk.Label(main_frame, text="Cursor Color (Light Mode):").grid(row=12, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=light_cursor_var).grid(row=12, column=1)

        tk.Label(main_frame, text="Current Font Family:").grid(row=13, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=font_family, state='readonly').grid(row=13, column=1)

        tk.Label(main_frame, text="Current Font Size:").grid(row=14, column=0, sticky="w")
        tk.Entry(main_frame, textvariable=font_size, state='readonly').grid(row=14, column=1)

        def apply_config():
            try:
                # Ensure all hex values are valid
                if not all(self.is_valid_hex_color(x) for x in (dark_fg_var.get(), dark_bg_var.get(), dark_ln_fg_var.get(), dark_cursor_var.get(), light_fg_var.get(), light_bg_var.get(), light_ln_fg_var.get(), light_cursor_var.get())):
                    raise ValueError("One or more color values are invalid.")

                # Ensure num_spaces_for_tab is a positive integer
                num_spaces = int(num_spaces_for_tab_var.get())
                if num_spaces <= 0:
                    raise ValueError("Number of spaces for tab should be a positive integer")

                # Save to the configuration file
                config = {
                    'word_wrap': self.word_wrap.get(),
                    'is_dark_mode': self.is_dark_mode.get(),
                    'use_spaces_for_tab': self.use_spaces_for_tab.get(),
                    'sticky_indentation': self.sticky_indentation.get(),
                    'tab_spaces': num_spaces,
                    'dark_fg': dark_fg_var.get(),
                    'dark_bg': dark_bg_var.get(),
                    'dark_ln_fg': dark_ln_fg_var.get(),
                    'dark_cursor': dark_cursor_var.get(),
                    'light_fg': light_fg_var.get(),
                    'light_bg': light_bg_var.get(),
                    'light_ln_fg': light_ln_fg_var.get(),
                    'light_cursor': light_cursor_var.get(),
                    'font_size': self.default_font_size,
                    'font_family': self.my_font,
                }
                config_manager = ConfigManager()
                config_manager.write_config(config)
                main_window.destroy()
                self.load_configurations()
                self.toggle_dark_mode()
            except ValueError as e:
                tk.messagebox.showerror("Invalid Value", str(e))

        tk.Button(main_frame, text="Apply", command=apply_config).grid(row=15, column=0, columnspan=2)

    #Load configurations
    def load_configurations(self):
        config_manager = ConfigManager()
        config = config_manager.read_config()

        if config:
            # Apply configurations
            self.is_dark_mode.set(config.get('is_dark_mode', self.is_dark_mode.get()))
            self.use_spaces_for_tab.set(config.get('use_spaces_for_tab', self.use_spaces_for_tab.get()))
            self.word_wrap.set(config.get('word_wrap', self.word_wrap.get()))
            self.sticky_indentation.set(config.get('sticky_indentation', self.sticky_indentation.get()))
            self.tab_spaces = config.get('tab_spaces', self.tab_spaces)
            self.default_font_size = config.get('font_size', self.default_font_size)
            self.my_font = config.get('font_family', self.my_font)

            # Color configurations
            self.dark_mode['fg'] = config.get('dark_fg', self.dark_mode['fg'])
            self.dark_mode['bg'] = config.get('dark_bg', self.dark_mode['bg'])
            self.dark_mode['fg-linenum'] = config.get('dark_ln_fg', self.dark_mode['fg-linenum'])
            self.dark_mode['insertbackground'] = config.get('dark_cursor', self.dark_mode['insertbackground'])

            self.light_mode['fg'] = config.get('light_fg', self.light_mode['fg'])
            self.light_mode['bg'] = config.get('light_bg', self.light_mode['bg'])
            self.light_mode['fg-linenum'] = config.get('light_ln_fg', self.light_mode['fg-linenum'])
            self.light_mode['insertbackground'] = config.get('light_cursor', self.light_mode['insertbackground'])

        # You can then apply these configurations to your text widget and other widgets as necessary.
        # For instance, you might change the colors of your text widget based on the dark mode setting, etc.



class ConfigManager:
    def __init__(self, filename='config.json'):
        self.filename = filename

    def read_config(self):
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return None

    def write_config(self, config):
        with open(self.filename, 'w') as file:
            json.dump(config, file, indent=4)


if __name__ == '__main__':
    root = tk.Tk()
    editor = TextWithLineNumbers(root)
    editor.create_menus()
    editor.pack(fill=tk.BOTH, expand=True)
    editor.toggle_word_wrap()
    root.mainloop()


