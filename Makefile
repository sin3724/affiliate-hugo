.PHONY: gen serve build clean
gen:
	@if [ -f scripts/generate_posts.py ]; then python scripts/generate_posts.py; else echo "(no generator)"; fi
serve:
	hugo server -D --disableFastRender
build:
	./build.sh
clean:
	rm -rf public
