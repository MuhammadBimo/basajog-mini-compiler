# symbol_table.py — Implementasi Tabel Simbol kanggo BasaJog


class Symbol:
    """Siji entri ing njero tabel simbol."""

    def __init__(self, name, type_, value=None, scope='global'):
        self.name  = name
        self.type  = type_   # 'int', 'float', 'string', 'bool', 'fungsi', 'unknown'
        self.value = value   # aji wektu-kompilasi (yen bisa dingerteni)
        self.scope = scope

    def __repr__(self):
        return (f"Symbol(name={self.name!r}, type={self.type!r}, "
                f"scope={self.scope!r}, value={self.value!r})")


class SymbolTable:
    """
    Tabel Simbol kanthi dhukungan scope susun-susun.
    Saben fungsi nggawe SymbolTable anyar kanthi parent = scope sing nyeluk.
    """

    def __init__(self, scope_name='global', parent=None):
        self.scope_name = scope_name
        self.parent     = parent
        self._symbols   = {}   # name -> Symbol

    # ----------------------------------------------------------
    # Operasi dhasar
    # ----------------------------------------------------------

    def define(self, name, type_, value=None):
        """Nambahake simbol anyar menyang scope saiki."""
        sym = Symbol(name, type_, value, self.scope_name)
        self._symbols[name] = sym
        return sym

    def lookup(self, name, local_only=False):
        """
        Nggoleki simbol. Yen local_only=False, golek uga menyang scope wong tuwa.
        Mbalekake Symbol utawa None.
        """
        if name in self._symbols:
            return self._symbols[name]
        if not local_only and self.parent is not None:
            return self.parent.lookup(name)
        return None

    def update_value(self, name, value):
        """Nganyari aji simbol (kanggo constant propagation)."""
        sym = self.lookup(name)
        if sym:
            sym.value = value

    def update_type(self, name, type_):
        """Nganyari jinis simbol."""
        sym = self.lookup(name)
        if sym:
            sym.type = type_

    def all_symbols(self):
        """Mbalekake kabeh simbol ing scope iki (ora kalebu wong tuwa)."""
        return list(self._symbols.values())

    # ----------------------------------------------------------
    # Nampilake tabel
    # ----------------------------------------------------------

    def print_table(self, show_parent=False):
        col = 55
        print(f"\n{'='*col}")
        print(f"  Tabel Simbol  --  Scope: '{self.scope_name}'")
        print(f"{'='*col}")
        print(f"  {'Jeneng':<14} {'Jinis':<10} {'Scope':<14} Aji")
        print(f"  {'-'*(col-2)}")

        if not self._symbols:
            print("  (kothong)")
        else:
            for sym in self._symbols.values():
                val = str(sym.value) if sym.value is not None else '-'
                print(f"  {sym.name:<14} {sym.type:<10} {sym.scope:<14} {val}")

        print(f"{'='*col}")

        if show_parent and self.parent:
            self.parent.print_table(show_parent=True)
