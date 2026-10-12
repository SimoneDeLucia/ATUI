// Raylib-Go Accelerated Thumbnail Engine for AndroidTUI
// Based on Raylib (https://www.raylib.com) via gen2brain/raylib-go (https://github.com/gen2brain/raylib-go)
// Generates high-performance truecolor half-block ANSI representations and scaled thumbnails for terminal preview.
package main

import (
	"fmt"
	"os"
	"strconv"
	"strings"

	rl "github.com/gen2brain/raylib-go/raylib"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: raylib-thumb <image_path> [max_width] [max_height] [output_thumb_file]\n")
		os.Exit(1)
	}

	imgPath := os.Args[1]
	maxWidth := int32(46)
	maxHeight := int32(20)

	// Silence internal Raylib debug traces
	rl.SetTraceLogLevel(rl.LogNone)

	if len(os.Args) >= 3 {
		if w, err := strconv.Atoi(os.Args[2]); err == nil && w > 0 {
			maxWidth = int32(w)
		}
	}
	if len(os.Args) >= 4 {
		if h, err := strconv.Atoi(os.Args[3]); err == nil && h > 0 {
			maxHeight = int32(h)
		}
	}

	img := rl.LoadImage(imgPath)
	if img.Width == 0 || img.Height == 0 {
		fmt.Fprintf(os.Stderr, "Error: Failed to load image '%s'\n", imgPath)
		os.Exit(2)
	}
	defer rl.UnloadImage(img)

	origW := img.Width
	origH := img.Height

	// Terminal cell aspect ratio: cells are roughly 2.0x taller than wide
	origAspect := float32(origW) / float32(origH)
	cellAspect := origAspect * 2.0

	targetW := maxWidth
	targetH := int32(float32(targetW) / cellAspect)

	if targetH > maxHeight {
		targetH = maxHeight
		targetW = int32(float32(targetH) * cellAspect)
	}
	if targetW < 1 {
		targetW = 1
	}
	if targetH < 1 {
		targetH = 1
	}

	pixelW := targetW
	pixelH := targetH * 2

	// Resize using Raylib bicubic filtering
	rl.ImageResize(img, pixelW, pixelH)

	// Export resized thumbnail to disk if 4th argument is given
	if len(os.Args) >= 5 && os.Args[4] != "--ansi" && os.Args[4] != "" {
		outPath := os.Args[4]
		if rl.ExportImage(*img, outPath) {
			fmt.Printf("THUMB_EXPORTED:%s:%dx%d\n", outPath, origW, origH)
			return
		}
	}

	// Output ANSI half-block (▀) representation to stdout
	fmt.Printf("DIM:%dx%d\n", origW, origH)

	var sb strings.Builder
	for y := int32(0); y < targetH; y++ {
		yTop := y * 2
		yBottom := y*2 + 1
		if yBottom >= pixelH {
			yBottom = pixelH - 1
		}

		for x := int32(0); x < pixelW; x++ {
			cTop := rl.GetImageColor(*img, x, yTop)
			cBottom := rl.GetImageColor(*img, x, yBottom)

			sb.WriteString(fmt.Sprintf("\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm▀",
				cTop.R, cTop.G, cTop.B,
				cBottom.R, cBottom.G, cBottom.B,
			))
		}
		sb.WriteString("\x1b[0m\n")
	}

	os.Stdout.WriteString(sb.String())
}
