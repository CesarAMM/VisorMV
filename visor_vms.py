import tkinter as tk
from tkinter import ttk, messagebox
import libvirt
import sys

class VisorVM:
    ## SECCION DE LA VENTA PRINCIPAL
    def __init__(self, root):
        self.root = root
        self.root.title("Maquinas Virtuales")
        self.root.geometry("700x450")

        label_titulo = tk.Label(root, text="Maquinas Virtuales", font=("Arial", 16, "bold"))
        label_titulo.pack(pady=10)

        self.tabla = ttk.Treeview(root, columns=("Nombre", "Estado"), show='headings')
        self.tabla.heading("Nombre", text="Nombre de la VM")
        self.tabla.heading("Estado", text="Estado Actual")
        self.tabla.pack(pady=20, padx=20, fill="both", expand=True)

        frame_botones = tk.Frame(root)
        frame_botones.pack(pady=10)

        btn_crear = tk.Button(frame_botones, text="Nueva VM", command=self.ventana_crear, bg="green", fg="white", width=12)
        btn_crear.grid(row=0, column=0, padx=5)

        btn_iniciar = tk.Button(frame_botones, text="Iniciar", command=self.iniciar_vm, bg="blue", fg="white", width=12)
        btn_iniciar.grid(row=0, column=1, padx=5)

        btn_detener = tk.Button(frame_botones, text="Detener", command=self.detener_vm, bg="red", fg="white", width=12)
        btn_detener.grid(row=0, column=2, padx=5)

        btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_vm, bg="red", fg="white", width=12)
        btn_eliminar.grid(row=1, column=1, padx=5)

        try:
            self.conn = libvirt.open('qemu:///system')
            if self.conn is None:
                print('Fallo al conectar con el hipervisor')
                sys.exit(1)
        except libvirt.libvirtError as e:
            print(f'Error de conexión: {e}')
            sys.exit(1)
        self.actualizar_lista()
    
    def actualizar_lista(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)

        try:
            dominios = self.conn.listAllDomains()
            
            for dom in dominios:
                nombre = dom.name()
                estado_id, _ = dom.state()
                
                estados = {
                    libvirt.VIR_DOMAIN_RUNNING: "Ejecutándose",
                    libvirt.VIR_DOMAIN_PAUSED: "Pausada",
                    libvirt.VIR_DOMAIN_SHUTOFF: "Apagada",
                    libvirt.VIR_DOMAIN_CRASHED: "Error"
                }
                estado_texto = estados.get(estado_id, "Desconocido")

                self.tabla.insert("", "end", values=(nombre, estado_texto))
                
        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"No se pudo obtener la lista: {e}")

    def iniciar_vm(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona una VM de la lista.")
            return

        item = self.tabla.item(seleccion)
        nombre_vm = item['values'][0]

        try:
            dom = self.conn.lookupByName(nombre_vm)
            
            dom.create()
            messagebox.showinfo("Éxito", f"La máquina '{nombre_vm}' se está iniciando.")
            
            self.actualizar_lista()
            
        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"No se pudo iniciar la VM: {e}")

    def detener_vm(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Selecciona una VM para detener.")
            return

        item = self.tabla.item(seleccion)
        nombre_vm = item['values'][0]

        try:
            dom = self.conn.lookupByName(nombre_vm)
            dom.destroy()
            messagebox.showinfo("Éxito", f"La máquina '{nombre_vm}' ha sido detenida.")
            
            self.actualizar_lista()
            
        except libvirt.libvirtError as e:
            messagebox.showerror("Error", f"No se pudo detener la VM: {e}")

    def eliminar_vm(self):
        seleccion = self.tabla.selection()
        if not seleccion: return
        
        nombre_vm = self.tabla.item(seleccion)['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar '{nombre_vm}'?"):
            try:
                dom = self.conn.lookupByName(nombre_vm)
                dom.undefine()
                self.actualizar_lista()
            except libvirt.libvirtError as e:
                messagebox.showerror("Error", str(e))

    ## SECCION PARA AGREGAR UNA MAQUINA NUEVA
    def ventana_crear(self):
        self.win_crear = tk.Toplevel(self.root)
        self.win_crear.title("Configurar Nueva VM")
        self.win_crear.geometry("300x250")

        tk.Label(self.win_crear, text="Nombre de la VM:").pack(pady=5)
        self.ent_nombre = tk.Entry(self.win_crear)
        self.ent_nombre.pack()

        tk.Label(self.win_crear, text="Memoria RAM (MB):").pack(pady=5)
        self.ent_ram = tk.Entry(self.win_crear)
        self.ent_ram.insert(0, "1024") # Valor por defecto
        self.ent_ram.pack()

        tk.Label(self.win_crear, text="CPUs:").pack(pady=5)
        self.ent_cpu = tk.Entry(self.win_crear)
        self.ent_cpu.insert(0, "1")
        self.ent_cpu.pack()

        tk.Button(self.win_crear, text="Crear Máquina", command=self.ejecutar_creacion, bg="green", fg="white").pack(pady=20)

    def ejecutar_creacion(self):
        nombre = self.ent_nombre.get()
        
        if not nombre:
            messagebox.showwarning("Error", "El nombre no puede estar vacío")
            return
            
        ram = int(self.ent_ram.get()) * 1024 
        cpu = self.ent_cpu.get()
        
        xml_config = f""" 
        <domain type='kvm'>
          <name>{nombre}</name>
          <memory unit='KiB'>{ram}</memory>
          <vcpu>{cpu}</vcpu>
          <os>
            <type arch='x86_64' machine='pc'>hvm</type>
          </os>
          <devices>
            <emulator>/usr/bin/qemu-system-x86_64</emulator>
            <interface type='user'>
              <model type='virtio'/>
            </interface>
            <graphics type='vnc' port='-1' autoport='yes'/>
          </devices>
        </domain>
        """

        try:
            self.conn.defineXML(xml_config)
            messagebox.showinfo("Éxito", f"Máquina '{nombre}' creada correctamente.")
            self.win_crear.destroy()
            self.actualizar_lista()
        except libvirt.libvirtError as e:
            messagebox.showerror("Error de Libvirt", f"Detalle técnico: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VisorVM(root)
    root.mainloop()