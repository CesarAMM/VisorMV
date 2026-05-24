import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import libvirt
import sys
import os
import subprocess

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

        btn_operar = tk.Button(frame_botones, text="Mostrar", command=self.def_operar_vm, bg="blue", fg="white", width=12)
        btn_operar.grid(row=0, column=3, padx=5)

        btn_eliminar = tk.Button(frame_botones, text="Eliminar", command=self.eliminar_vm, bg="red", fg="white", width=12)
        btn_eliminar.grid(row=0, column=4, padx=5)

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

    def def_operar_vm(self):
        # 1. Obtener la máquina seleccionada de la tabla
        seleccion = self.tabla.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona una máquina de la lista para operar.")
            return

        nombre_vm = self.tabla.item(seleccion)['values'][0]

        try:
            # 2. Buscar el objeto de la máquina en Libvirt
            dom = self.conn.lookupByName(nombre_vm)
            
            # 3. Validar si la máquina está encendida (Si está apagada, no hay señal de video)
            if not dom.isActive():
                messagebox.showwarning("Máquina Apagada", f"La máquina '{nombre_vm}' debe estar 'Ejecutándose' para poder operar en ella. Iníciala primero.")
                return

            # 4. Lanzar la ventana del visor de manera asíncrona usando Popen
            # Esto evita que tu ventana de Tkinter se quede congelada mientras usas la VM
            subprocess.Popen(
                ["virt-viewer", "--connect", "qemu:///system", "--wait", nombre_vm],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        except libvirt.libvirtError as e:
            messagebox.showerror("Error de Libvirt", f"No se pudo conectar con la consola de la VM: {e}")
        except FileNotFoundError:
            messagebox.showerror("Dependencia Faltante", "No se encontró 'virt-viewer' en el sistema. Ejecuta en tu terminal: sudo apt install virt-viewer")

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

        if not seleccion:
            messagebox.showwarning("Advertencia", "Por favor, seleccione una máquina virtual para eliminar.")
            return
        
        nombre_vm = self.tabla.item(seleccion)['values'][0]
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar '{nombre_vm}'?"):
            try:
                dom = self.conn.lookupByName(nombre_vm)
                
                if dom.isActive():
                    messagebox.showerror(
                        "Error de Eliminación", 
                        f"La máquina '{nombre_vm}' está actualmente EN EJECUCIÓN.\n\nDebe detenerla (apagarla) antes de poder eliminarla."
                    )
                    return
                
                dom.undefine()
                self.actualizar_lista()
            except libvirt.libvirtError as e:
                messagebox.showerror("Error", str(e))

    def seleccionar_iso(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar imagen ISO",
            filetypes=[("Archivos ISO", "*.iso"), ("Todos los archivos", "*.*")]
        )
        if ruta: 
            self.ent_iso.delete(0, tk.END)
            self.ent_iso.insert(0, ruta)

    def seleccionar_carpeta_disco(self):
        ruta = filedialog.askdirectory(
            title="Seleccionar carpeta para el Disco Duro"
        )
        if ruta:
            self.ent_ruta_disk.delete(0, tk.END)
            self.ent_ruta_disk.insert(0, ruta)

    ## SECCION PARA AGREGAR UNA MAQUINA NUEVA
    def ventana_crear(self):
        self.win_crear = tk.Toplevel(self.root)
        self.win_crear.title("Configurar Nueva VM")
        self.win_crear.geometry("700x350")

        frame_formulario = tk.Frame(self.win_crear)
        frame_formulario.pack(pady=20, padx=1)

        ## FILA 1
        tk.Label(frame_formulario, text="Nombre de la MV: ", anchor="w", width=15).grid(row=0, column=0, padx=1, pady=2)
        self.entNombre = tk.Entry(frame_formulario)
        self.entNombre.grid(row=0, column=1, columnspan=3, sticky="ew", padx=2, pady=2)
        
        ## FILA 2
        tk.Label(frame_formulario, text="Ruta ISO:", anchor="w", width=15).grid(row=1, column=0, padx=1, pady=2)
        frame_iso = tk.Frame(frame_formulario)
        frame_iso.grid(row=1, column=1, columnspan=3, sticky="ew", padx=2, pady=2)
        self.ent_iso = tk.Entry(frame_iso, width=55)
        self.ent_iso.pack(side="left")
        tk.Button(frame_iso, text="📁", command=self.seleccionar_iso).pack(side="right", padx=2)


        tk.Label(frame_formulario, text="Ruta DISK:", anchor="w", width=15).grid(row=2, column=0, padx=1, pady=2)
        frame_disk = tk.Frame(frame_formulario)
        frame_disk.grid(row=2, column=1,columnspan=3, sticky="ew", padx=2, pady=2)
        self.ent_ruta_disk = tk.Entry(frame_disk, width=55)
        self.ent_ruta_disk.pack(side="left")
        tk.Button(frame_disk, text="📁", command=self.seleccionar_carpeta_disco).pack(side="right", padx=2)

        ## FILA 3
        tk.Label(frame_formulario, text="Espacio DISK:", anchor="w", width=15).grid(row=3, column=0, padx=1, pady=2)
        self.ent_spec_disk = tk.Entry(frame_formulario)
        self.ent_spec_disk.grid(row=3, column=1, padx=1, pady=2)
        self.ent_spec_disk.insert(0, "20")

        tk.Label(frame_formulario, text="Memoria RAM (MB):", anchor="w", width=15).grid(row=3, column=2, padx=1, pady=2)
        self.ent_ram = tk.Entry(frame_formulario)
        self.ent_ram.grid(row=3, column=3, padx=1, pady=2)
        self.ent_ram.insert(0, "1024") # Valor por defecto

        tk.Label(frame_formulario, text="CPUS:", anchor="w", width=15).grid(row=4, column=0, padx=1, pady=2)
        self.ent_cpu = tk.Entry(frame_formulario)
        self.ent_cpu.grid(row=4, column=1, padx=1, pady=2)
        self.ent_cpu.insert(0, "1")

        tk.Button(frame_formulario, text="Crear Máquina", command=self.ejecutar_creacion, bg="green", fg="white").grid(row=5, column=0, padx=1, pady=10, columnspan=2)

    def ejecutar_creacion(self):
        nombre = self.entNombre.get()
        ruta_disk = self.ent_ruta_disk.get()
        ruta_iso = self.ent_iso.get()
        ram = int(self.ent_ram.get()) * 1024 
        cpu = self.ent_cpu.get()
        disk = int(self.ent_spec_disk.get())

        if not ruta_disk:
            messagebox.showerror("Error Disk", "La ruta esta vacio.")
            return

        if not ruta_iso:
            messagebox.showerror("Error ISO", "La ruta ISO esta vacio.")
            return

        if not nombre:
            messagebox.showwarning("Error", "El nombre no puede estar vacío.")
            return
            
        if not nombre:
            messagebox.showwarning("Error", "El nombre no puede estar vacío.")
            return
        
        if not disk:
            messagebox.showwarning("Error", "El espacio de disco no puede estar vacio.")
            return

        if disk < 20 :
            messagebox.showwarning("Error", "El espacio de disco debe ser mayor o igual a 20[G]")
            return
        
        ruta_completa_disk = os.path.join(ruta_disk, f"{nombre}.qcow2")
        
        try:
            subprocess.run(
                ["qemu-img", "create", "-f", "qcow2", ruta_completa_disk, f"{disk}G"],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error crear Disco", f"Detalle técnico: {e.stderr.decode()}")
        
        xml_config = f"""
            <domain type='kvm'>
                <name>{nombre}</name>
                <memory unit='KiB'>{ram}</memory>
                <vcpu>{cpu}</vcpu>
                
                <os>
                    <type arch='x86_64' machine='pc'>hvm</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                </os>
          
                <devices>
                    <emulator>/usr/bin/qemu-system-x86_64</emulator>
            
                    <disk type='file' device='disk'>
                        <driver name='qemu' type='qcow2'/>
                        <source file='{ruta_completa_disk}'/>
                        <target dev='vda' bus='virtio'/> 
                    </disk>

                    <disk type='file' device='cdrom'>
                        <driver name='qemu' type='raw'/>
                        <source file='{ruta_iso}'/>
                        <target dev='sda' bus='sata'/>
                        <readonly/>
                    </disk>

                    <interface type='network'>
                        <source network='default'/>
                        <model type='virtio'/>
                    </interface>

                    <interface type='user'>
                        <model type='virtio'/>
                    </interface>
            
                    <graphics type='vnc' port='-1' autoport='yes'/>

                    <video>
                        <model type='virtio'/>
                    </video>
                </devices>
            </domain>
        """
        try:
            self.conn.defineXML(xml_config)
            self.win_crear.destroy()
            messagebox.showinfo("Éxito", f"Máquina '{nombre}' creada correctamente.")
            self.actualizar_lista()
        except libvirt.libvirtError as e:
            messagebox.showerror("Error de Libvirt", f"Detalle técnico: {e}")



if __name__ == "__main__":
    root = tk.Tk()
    app = VisorVM(root)
    root.mainloop()