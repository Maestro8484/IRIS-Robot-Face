#pragma once

#include "eyes/eyes.h"

// Default eye: nordicBlue (both displays)
#include "eyes/240x240/nordicBlue.h"
// flame: used for ANGRY emotion swap
#include "eyes/240x240/flame.h"
#include "eyes/EyeController.h"

#define USE_GC9A01A
//#define USE_ST7789

#ifdef USE_GC9A01A
#include "displays/GC9A01A_Display.h"
#elif defined USE_ST7789
#include "displays/ST7789_Display.h"
#ifdef ST7735_SPICLOCK
#undef ST7735_SPICLOCK
#endif
#define ST7735_SPICLOCK 30'000'000
#endif

// Index 0: nordicBlue (default)
// Index 1: flame (ANGRY emotion)
std::array<std::array<EyeDefinition, 2>, 2> eyeDefinitions{{
    {nordicBlue::eye, nordicBlue::eye},
    {flame::eye,      flame::eye},
}};

#ifdef USE_GC9A01A
GC9A01A_Config eyeInfo[] = {
    // CS DC MOSI SCK RST ROT MIRROR USE_FB ASYNC
    {0,  2, 26, 27, 3,  0, true,  true, false}, // Left  -- nordicBlue / flame
    {10, 9, 11, 13, -1, 0, false, true, false}, // Right -- nordicBlue / flame
};
#elif defined USE_ST7789
ST7789_Config eyeInfo[] = {
    {-1,  2, 26, 27, 3, 0, true,  true, true},
    {-1,  9, 11, 13, 8, 0, false, true, true},
};
#endif

constexpr uint32_t EYE_DURATION_MS{10'000};
constexpr uint32_t SPI_SPEED{20'000'000};

constexpr int8_t BLINK_PIN{-1};
constexpr int8_t JOYSTICK_X_PIN{-1};
constexpr int8_t JOYSTICK_Y_PIN{-1};
constexpr int8_t LIGHT_PIN{-1};
constexpr bool USE_PERSON_SENSOR{true};

#ifdef USE_GC9A01A
EyeController<2, GC9A01A_Display> *eyes{};
// Global display pointers -- used by blankDisplays() in main.cpp
GC9A01A_Display *displayLeft{};
GC9A01A_Display *displayRight{};
#elif defined USE_ST7789
EyeController<2, ST7789_Display> *eyes{};
#endif

void initEyes(bool autoMove, bool autoBlink, bool autoPupils) {
  auto &defs = eyeDefinitions.at(0);
#ifdef USE_GC9A01A
  displayLeft  = new GC9A01A_Display(eyeInfo[0], SPI_SPEED);
  displayRight = new GC9A01A_Display(eyeInfo[1], SPI_SPEED);
  const DisplayDefinition<GC9A01A_Display> left{displayLeft,  defs[0]};
  const DisplayDefinition<GC9A01A_Display> right{displayRight, defs[1]};
  eyes = new EyeController<2, GC9A01A_Display>({left, right}, autoMove, autoBlink, autoPupils);
#elif defined USE_ST7789
  auto l = new ST7789_Display(eyeInfo[0]);
  auto r = new ST7789_Display(eyeInfo[1]);
  const DisplayDefinition<ST7789_Display> left{l, defs[0]};
  const DisplayDefinition<ST7789_Display> right{r, defs[1]};
  eyes = new EyeController<2, ST7789_Display>({left, right}, autoMove, autoBlink, autoPupils);
#endif
}
