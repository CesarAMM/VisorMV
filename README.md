# VisorMV

## Dependencias del Sistema (Virtualizacion)

- qemu-kvm: Actua como el emulador y el hipervisor principal del entorno
- libvirt: Es el servicio que se ejecuta en segundo plano para permitir gestion de las maquinas virtuales
- virt-manager: es la herramienta para visualizar y hacer pruebas que instale correctamente las maquinas virutales el proyecto VisorMV

## Librerias de Python

- libvirt-python: Es la biblioteca necesaria para que tu script de Python pueda comunicarse con el hipervisor y gestionar los recursos
- tkinter: Es la librería empleada para diseñar y construir toda la interfaz gráfica de tu visor (la ventana principal, los formularios y los botones). Aunque normalmente viene incluida por defecto con Python, en ciertas distribuciones de Linux requiere instalarse por separado (por ejemplo, mediante el paquete


## Configuaraciones del libvirt

`` susdo nano etc/libvirt/qemu.conf ``

se debe de modificar: ``` user = "usuario" ```
