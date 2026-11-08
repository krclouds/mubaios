/*
 * Files -- browse the mubaiOS filesystem.
 */
#define _GNU_SOURCE
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#include "nova.h"

static int ptr_x = 200, ptr_y = 200;
#define REDRAW(call) do { nova_cursor_reset(); call; nova_cursor_draw(&fb, ptr_x, ptr_y); } while (0)

struct entry {
	char name[128];
	int is_dir;
	long size;
};

static struct entry entries[128];
static int entry_count;
static char cwd[256] = "/";
static int scroll;
static int preview;
static char preview_path[300];
static char preview_lines[18][160];
static int preview_count;

static int cmp_entry(const void *a, const void *b)
{
	const struct entry *x = a, *y = b;

	if (x->is_dir != y->is_dir)
		return y->is_dir - x->is_dir;
	return strcmp(x->name, y->name);
}

static void load_dir(void)
{
	DIR *d = opendir(cwd);
	struct dirent *de;

	entry_count = 0;
	scroll = 0;
	if (!d)
		return;
	while ((de = readdir(d)) && entry_count < 128) {
		struct stat st;
		char path[512];

		if (de->d_name[0] == '.')
			continue;
		snprintf(path, sizeof(path), "%s/%s", strcmp(cwd, "/") ? cwd : "", de->d_name);
		if (stat(path, &st) != 0)
			continue;
		snprintf(entries[entry_count].name, sizeof(entries[entry_count].name), "%s", de->d_name);
		entries[entry_count].is_dir = S_ISDIR(st.st_mode);
		entries[entry_count].size = (long)st.st_size;
		entry_count++;
	}
	closedir(d);
	qsort(entries, entry_count, sizeof(entries[0]), cmp_entry);
}

static void open_file(const char *path)
{
	FILE *f = fopen(path, "r");
	char line[160];

	preview = 1;
	preview_count = 0;
	snprintf(preview_path, sizeof(preview_path), "%s", path);
	if (!f)
		return;
	while (preview_count < 18 && fgets(line, sizeof(line), f)) {
		line[strcspn(line, "\n")] = '\0';
		snprintf(preview_lines[preview_count], sizeof(preview_lines[0]), "%s", line);
		preview_count++;
	}
	fclose(f);
}

static void draw(NovaFB *fb, int selected)
{
	nova_app_header(fb, "文件");
	nova_text(fb, 60, 146, cwd, NOVA_DIM, 2);

	int y = 180;
	for (int i = scroll; i < entry_count && y < fb->h - 90; i++) {
		uint32_t bg = (i == selected) ? 0x2c3350 : 0x1b2030;
		nova_round_rect(fb, 50, y, fb->w - 100, 54, 12, bg);
		nova_text(fb, 76, y + 14, entries[i].is_dir ? "[D]" : "   ", NOVA_DIM, 2);
		nova_text(fb, 140, y + 14, entries[i].name, entries[i].is_dir ? 0x9fd4ff : NOVA_TEXT, 2);
		if (!entries[i].is_dir) {
			char sz[32];
			snprintf(sz, sizeof(sz), "%ld B", entries[i].size);
			nova_text(fb, fb->w - 160, y + 14, sz, NOVA_DIM, 2);
		}
		y += 62;
	}
	if (entry_count == 0)
		nova_text(fb, 60, 200, "空目录", NOVA_DIM, 2);
}

static void draw_preview(NovaFB *fb)
{
	nova_app_header(fb, "查看器");
	nova_text(fb, 60, 146, preview_path, NOVA_DIM, 2);
	for (int i = 0; i < preview_count; i++)
		nova_text(fb, 60, 186 + i * 26, preview_lines[i], NOVA_TEXT, 1);
	if (preview_count == 0)
		nova_text(fb, 60, 186, "(二进制或空文件)", NOVA_DIM, 2);
}

int main(void)
{
	NovaFB fb;
	NovaInput in;
	NovaEvent ev;
	int selected = -1;

	if (nova_fb_open(&fb) < 0)
		return 1;
	nova_set_screen(fb.w, fb.h);
	if (nova_input_open(&in) < 0)
		return 1;

	load_dir();
	draw(&fb, selected);

	for (;;) {
		if (nova_poll(&in, &ev, 500) == 0)
			continue;
		ptr_x = ev.x;
		ptr_y = ev.y;
		if (ev.type == NOVA_MOVE) {
			nova_cursor_draw(&fb, ev.x, ev.y);
			continue;
		}
		if (ev.type == NOVA_KEY && ev.key == 1)
			return 0;

		if (ev.type == NOVA_WHEEL) {
			scroll += ev.value * 2;
			if (scroll < 0)
				scroll = 0;
			if (scroll >= entry_count)
				scroll = entry_count > 0 ? entry_count - 1 : 0;
			if (preview)
				REDRAW(draw_preview(&fb));
			else
				draw(&fb, selected);
			continue;
		}

		if (ev.type == NOVA_DOWN && nova_back_hit(ev.x, ev.y)) {
			if (preview) {
				preview = 0;
				draw(&fb, selected);
			} else if (strcmp(cwd, "/") != 0) {
				char *slash = strrchr(cwd, '/');
				if (slash == cwd)
					cwd[1] = '\0';
				else if (slash)
					*slash = '\0';
				load_dir();
				draw(&fb, selected);
			} else {
				return 0;
			}
			continue;
		}

		if (ev.type == NOVA_DOWN && !preview) {
			int idx = scroll + (ev.y - 180) / 62;
			if (ev.y >= 180 && idx >= 0 && idx < entry_count) {
				char path[512];

				selected = idx;
				snprintf(path, sizeof(path), "%s/%s",
					 strcmp(cwd, "/") ? cwd : "", entries[idx].name);
				if (entries[idx].is_dir) {
					snprintf(cwd, sizeof(cwd), "%s", path);
					load_dir();
					draw(&fb, selected);
				} else {
					open_file(path);
					REDRAW(draw_preview(&fb));
				}
			}
		}
	}
}
