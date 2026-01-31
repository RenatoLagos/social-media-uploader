#!/usr/bin/env python3
"""
Social Media Video Uploader - CLI Principal

Automatiza la subida de videos cortos a YouTube Shorts, Instagram Reels y TikTok
con transcripcion y descripciones optimizadas por IA.

Uso:
    python upload.py VIDEO_PATH [opciones]

Ejemplos:
    python upload.py C:\\videos\\mi_video.mp4
    python upload.py video.mp4 --only-youtube
    python upload.py video.mp4 --title "Mi video genial"
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import VideoUploadOrchestrator
from src.config.settings import settings

# Configurar consola para Windows (evitar errores de encoding)
console = Console(force_terminal=True, legacy_windows=True)


def print_header():
    """Mostrar header de la aplicacion"""
    console.print()
    console.print(Panel.fit(
        "[bold cyan]Social Media Video Uploader[/bold cyan]\n"
        "[dim]YouTube Shorts | Instagram Reels | TikTok[/dim]",
        border_style="cyan"
    ))
    console.print()


def print_results(result):
    """Mostrar resultados en tabla"""
    # Tabla de resultados de upload
    table = Table(title="Resultados de Upload", show_header=True)
    table.add_column("Plataforma", style="cyan", width=12)
    table.add_column("Estado", style="bold", width=10)
    table.add_column("URL / Error", style="dim", overflow="fold")

    for upload in result.upload_results:
        if upload.success:
            status = "[green]Exito[/green]"
            detail = upload.url or "OK"
        else:
            status = "[red]Fallo[/red]"
            detail = upload.error or "Error desconocido"

        table.add_row(upload.platform, status, detail)

    console.print(table)

    # Resumen
    console.print()
    successful = result.successful_uploads
    total = result.total_uploads

    if successful == total:
        console.print(f"[bold green]Todos los uploads exitosos ({successful}/{total})[/bold green]")
    elif successful > 0:
        console.print(f"[bold yellow]{successful}/{total} uploads exitosos[/bold yellow]")
    else:
        console.print(f"[bold red]Todos los uploads fallaron ({successful}/{total})[/bold red]")


def print_metadata(metadata):
    """Mostrar metadata del video"""
    console.print("[dim]Video:[/dim]", metadata.path)
    console.print(
        f"[dim]Info:[/dim] {metadata.duration:.1f}s | "
        f"{metadata.resolution[0]}x{metadata.resolution[1]} | "
        f"{metadata.file_size}MB | {metadata.aspect_ratio}"
    )


def print_transcription(transcription):
    """Mostrar preview de transcripcion"""
    preview = transcription[:200] + "..." if len(transcription) > 200 else transcription
    console.print(f"[dim]Transcripcion:[/dim] {preview}")


def print_descriptions_panel(descriptions, transcription=None):
    """Mostrar panel con descripciones generadas para cada plataforma"""

    # Mostrar transcripcion primero
    if transcription:
        console.print(Panel(
            transcription,
            title="[bold cyan]Transcripcion del Video[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()

    # Panel de YouTube (titulo + descripcion)
    youtube_content = f"[bold]TITLE:[/bold] {descriptions.youtube_title}\n\n[bold]DESCRIPTION:[/bold]\n{descriptions.youtube}"
    console.print(Panel(
        youtube_content,
        title="[bold red]YouTube Shorts[/bold red]",
        subtitle=f"[dim]Title: {len(descriptions.youtube_title)} chars | Desc: {len(descriptions.youtube)} chars[/dim]",
        border_style="red",
        padding=(1, 2)
    ))
    console.print()

    # Panel de Instagram
    console.print(Panel(
        descriptions.instagram,
        title="[bold magenta]Instagram Reels[/bold magenta]",
        subtitle=f"[dim]{len(descriptions.instagram)} caracteres[/dim]",
        border_style="magenta",
        padding=(1, 2)
    ))
    console.print()

    # Panel de TikTok (si esta habilitado)
    if descriptions.tiktok:
        console.print(Panel(
            descriptions.tiktok,
            title="[bold cyan]TikTok[/bold cyan]",
            subtitle=f"[dim]{len(descriptions.tiktok)} caracteres[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))
        console.print()


def edit_description(platform: str, current: str) -> str:
    """Permitir editar una descripcion"""
    console.print(f"\n[yellow]Editando descripcion de {platform}[/yellow]")
    console.print("[dim]Ingresa la nueva descripcion (Enter dos veces para terminar, 'cancel' para mantener original):[/dim]\n")

    lines = []
    empty_count = 0

    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
            lines.append("")
        else:
            empty_count = 0
            if line.lower() == "cancel":
                return current
            lines.append(line)

    new_desc = "\n".join(lines).strip()
    return new_desc if new_desc else current


def edit_title(current: str) -> str:
    """Permitir editar un titulo (una sola linea)"""
    console.print(f"\n[yellow]Titulo actual:[/yellow] {current}")
    new_title = console.input("[yellow]Nuevo titulo (Enter para mantener): [/yellow]").strip()
    return new_title if new_title else current


def confirm_and_edit_descriptions(descriptions, enabled_platforms):
    """Mostrar descripciones y permitir editar antes de subir"""

    while True:
        console.print("\n[bold]Opciones:[/bold]")
        console.print("  [green]s[/green] - Subir con estas descripciones")
        if 'YouTube' in enabled_platforms:
            console.print("  [yellow]yt[/yellow] - Editar titulo de YouTube")
            console.print("  [yellow]yd[/yellow] - Editar descripcion de YouTube")
        if 'Instagram' in enabled_platforms:
            console.print("  [yellow]i[/yellow] - Editar descripcion de Instagram")
        if 'TikTok' in enabled_platforms:
            console.print("  [yellow]t[/yellow] - Editar descripcion de TikTok")
        console.print("  [red]c[/red] - Cancelar")

        choice = console.input("\n[bold]Elige una opcion: [/bold]").lower().strip()

        if choice == 's':
            return descriptions, True
        elif choice == 'yt' and 'YouTube' in enabled_platforms:
            descriptions.youtube_title = edit_title(descriptions.youtube_title)
            console.print(f"[green]Titulo actualizado:[/green] {descriptions.youtube_title}")
        elif choice == 'yd' and 'YouTube' in enabled_platforms:
            descriptions.youtube = edit_description("YouTube", descriptions.youtube)
            console.print(Panel(descriptions.youtube, title="[bold red]YouTube Desc (editado)[/bold red]", border_style="red"))
        elif choice == 'i' and 'Instagram' in enabled_platforms:
            descriptions.instagram = edit_description("Instagram", descriptions.instagram)
            console.print(Panel(descriptions.instagram, title="[bold magenta]Instagram (editado)[/bold magenta]", border_style="magenta"))
        elif choice == 't' and 'TikTok' in enabled_platforms:
            descriptions.tiktok = edit_description("TikTok", descriptions.tiktok)
            console.print(Panel(descriptions.tiktok, title="[bold cyan]TikTok (editado)[/bold cyan]", border_style="cyan"))
        elif choice == 'c':
            return descriptions, False
        else:
            console.print("[red]Opcion no valida[/red]")


@click.command()
@click.argument('video_path', type=click.Path(exists=True))
@click.option(
    '--title', '-t',
    help='Titulo personalizado para el video'
)
@click.option(
    '--only-youtube', is_flag=True,
    help='Solo subir a YouTube'
)
@click.option(
    '--only-instagram', is_flag=True,
    help='Solo subir a Instagram'
)
@click.option(
    '--only-tiktok', is_flag=True,
    help='Solo subir a TikTok'
)
@click.option(
    '--skip-youtube', is_flag=True,
    help='Saltar YouTube'
)
@click.option(
    '--skip-instagram', is_flag=True,
    help='Saltar Instagram'
)
@click.option(
    '--skip-tiktok', is_flag=True,
    help='Saltar TikTok'
)
@click.option(
    '--check-config', is_flag=True,
    help='Solo verificar configuracion sin subir'
)
@click.option(
    '--preview', '-p', is_flag=True,
    help='Mostrar descripciones para revisar antes de subir'
)
@click.option(
    '--no-confirm', is_flag=True,
    help='Subir sin pedir confirmacion'
)
@click.option(
    '--verbose', '-v', is_flag=True,
    help='Mostrar logs detallados'
)
def main(
    video_path,
    title,
    only_youtube,
    only_instagram,
    only_tiktok,
    skip_youtube,
    skip_instagram,
    skip_tiktok,
    check_config,
    preview,
    no_confirm,
    verbose
):
    """
    Subir video corto a YouTube Shorts, Instagram Reels y TikTok.

    VIDEO_PATH: Ruta al archivo de video MP4 a subir.
    """
    print_header()

    # Determinar plataformas habilitadas
    if only_youtube:
        enable_yt, enable_ig, enable_tt = True, False, False
    elif only_instagram:
        enable_yt, enable_ig, enable_tt = False, True, False
    elif only_tiktok:
        enable_yt, enable_ig, enable_tt = False, False, True
    else:
        enable_yt = settings.enable_youtube and not skip_youtube
        enable_ig = settings.enable_instagram and not skip_instagram
        enable_tt = settings.enable_tiktok and not skip_tiktok

    try:
        # Inicializar orchestrador
        orchestrator = VideoUploadOrchestrator(
            enable_youtube=enable_yt,
            enable_instagram=enable_ig,
            enable_tiktok=enable_tt
        )

        # Verificar configuracion
        if check_config:
            console.print("[bold]Verificando configuracion...[/bold]\n")
            config_status = orchestrator.check_configuration()

            for service, configured in config_status.items():
                status = "[green]OK[/green]" if configured else "[red]No configurado[/red]"
                console.print(f"  {service.capitalize()}: {status}")

            console.print()
            return

        # Mostrar plataformas habilitadas
        platforms = orchestrator.get_enabled_platforms()
        if not platforms:
            console.print("[red]Error: No hay plataformas habilitadas[/red]")
            raise click.Abort()

        console.print(f"[dim]Plataformas:[/dim] {', '.join(platforms)}\n")

        # Paso 1: Validar video
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validando video...", total=None)
            metadata = orchestrator._validate_video(video_path)

        print_metadata(metadata)
        console.print()

        # Paso 2: Transcribir (o usar archivo existente)
        video_file = Path(video_path)
        txt_file = video_file.with_suffix('.txt')
        srt_file = video_file.with_suffix('.srt')

        if txt_file.exists():
            transcription_source = f"archivo .txt: {txt_file.name}"
        elif srt_file.exists():
            transcription_source = f"archivo .srt: {srt_file.name}"
        else:
            transcription_source = "Whisper API"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if transcription_source.startswith("archivo"):
                task = progress.add_task(f"Leyendo transcripcion de {transcription_source}...", total=None)
            else:
                task = progress.add_task("Transcribiendo audio con Whisper...", total=None)
            transcription = orchestrator._transcribe(video_path)

        console.print(f"[dim]Transcripcion:[/dim] desde {transcription_source}")
        console.print()

        # Paso 3: Generar descripciones
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generando descripciones con IA...", total=None)
            descriptions = orchestrator._generate_descriptions(transcription)

        console.print()

        # Mostrar panel de descripciones
        print_descriptions_panel(descriptions, transcription)

        # Si solo preview, terminar aqui
        if preview:
            console.print("[dim]Modo preview - no se subio nada[/dim]")
            return

        # Confirmar antes de subir (a menos que --no-confirm)
        if not no_confirm:
            descriptions, should_upload = confirm_and_edit_descriptions(descriptions, platforms)
            if not should_upload:
                console.print("\n[yellow]Upload cancelado[/yellow]")
                return

        # Paso 4: Subir a plataformas
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Subiendo a plataformas...", total=None)

            from src.models.video_metadata import ProcessingResult
            result = ProcessingResult(video_path=video_path)
            result.metadata = metadata
            result.transcription = transcription
            result.descriptions = descriptions

            # Usar titulo generado por IA si no se especifico uno manual
            youtube_title = title or descriptions.youtube_title

            result.upload_results = orchestrator._upload_to_platforms(
                video_path=video_path,
                descriptions=descriptions,
                title=youtube_title
            )

        console.print()
        print_results(result)
        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]Operacion cancelada por el usuario[/yellow]")
        sys.exit(1)

    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


@click.command()
def check():
    """Verificar configuracion del sistema"""
    print_header()

    orchestrator = VideoUploadOrchestrator()
    config_status = orchestrator.check_configuration()

    table = Table(title="Estado de Configuracion")
    table.add_column("Servicio", style="cyan")
    table.add_column("Estado", style="bold")

    for service, configured in config_status.items():
        status = "[green]Configurado[/green]" if configured else "[red]No configurado[/red]"
        table.add_row(service.capitalize(), status)

    console.print(table)


if __name__ == '__main__':
    main()
