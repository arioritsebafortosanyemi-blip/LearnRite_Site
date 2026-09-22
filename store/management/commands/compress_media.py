import os

from django.conf import settings
from django.core.management.base import BaseCommand
from PIL import Image

MAX_DIM = 900


class Command(BaseCommand):
    help = (
        "Re-compress every JPEG/PNG under MEDIA_ROOT in place (resize if larger "
        "than 900px on the long edge, re-encode at web-appropriate quality). "
        "Run this once on the production disk after a deploy that doesn't ship "
        "media/ changes via git (e.g. Render persistent disk)."
    )

    def handle(self, *args, **options):
        root = settings.MEDIA_ROOT
        total_before = 0
        total_after = 0
        changed = 0

        for dirpath, _, files in os.walk(root):
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext not in (".jpg", ".jpeg", ".png"):
                    continue
                path = os.path.join(dirpath, name)
                before = os.path.getsize(path)
                total_before += before

                img = Image.open(path)
                has_alpha = ext == ".png" and (
                    img.mode in ("RGBA", "LA")
                    or (img.mode == "P" and "transparency" in img.info)
                )
                img = img.convert("RGBA") if has_alpha else img.convert("RGB")

                if max(img.size) > MAX_DIM:
                    ratio = MAX_DIM / max(img.size)
                    img = img.resize(
                        (round(img.width * ratio), round(img.height * ratio)),
                        Image.LANCZOS,
                    )

                if has_alpha:
                    img.save(path, "PNG", optimize=True)
                else:
                    img.save(path, "JPEG", quality=80, optimize=True, progressive=True)

                after = os.path.getsize(path)
                total_after += after
                if after != before:
                    changed += 1
                    rel = os.path.relpath(path, root)
                    self.stdout.write(f"{rel}: {before} -> {after}")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. {changed} files changed. "
            f"{total_before/1024/1024:.2f}MB -> {total_after/1024/1024:.2f}MB "
            f"(saved {(total_before-total_after)/1024/1024:.2f}MB)"
        ))
