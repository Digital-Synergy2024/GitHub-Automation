import customtkinter as ctk  # type: ignore

def main():
    root = ctk.CTk()
    root.title("GitHub Manager - Minimal Test")
    root.geometry("800x700")

    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=10, pady=10)

    main_tab = tabview.add("Main")
    ctk.CTkLabel(main_tab, text="Main Tab Loaded").pack(pady=20)

    repos_tab = tabview.add("Repositories")
    ctk.CTkLabel(repos_tab, text="Repositories Tab Loaded").pack(pady=20)

    instructions_tab = tabview.add("Instructions")
    ctk.CTkLabel(instructions_tab, text="Instructions Tab Loaded").pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()