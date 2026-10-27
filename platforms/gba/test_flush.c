#include <tonc.h>

#define REG_DEBUG_ENABLE (*(volatile u16 *)0x4FFF780)
#define REG_DEBUG_FLAGS  (*(volatile u16 *)0x4FFF700)
#define REG_DEBUG_STRING ((char *)0x4FFF600)

static void mgba_log(const char *msg)
{
	REG_DEBUG_ENABLE = 0xC0DE;
	int i = 0;
	while (msg[i] && i < 255) {
		REG_DEBUG_STRING[i] = msg[i];
		i++;
	}
	REG_DEBUG_STRING[i] = '\0';
	REG_DEBUG_FLAGS = 0x103;
}

int main(void)
{
	REG_DISPCNT = DCNT_MODE3 | DCNT_BG2;
	for (int i = 0; i < 20; i++) {
		mgba_log("LOOP LOG MESSAGE");
	}
	for (;;) {
		VBlankIntrWait();
	}
	return 0;
}
