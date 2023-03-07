.DEFAULT_GOAL := all

TARGET_DIR=/Volumes/CIRCUITPY
LIB_DIR=$(TARGET_DIR)/lib

CODE=$(addprefix $(TARGET_DIR)/, code.py secrets.py)
LIBS=$(addprefix $(LIB_DIR)/, adafruit_requests.mpy adafruit_progressbar adafruit_display_text)

$(TARGET_DIR)/%.py: %.py
	cp $< $@

$(TARGET_DIR)/lib/%: lib/%
	rsync -a $< $(TARGET_DIR)/lib

$(LIB_DIR): 
	mkdir $@

$(LIBS): | $(LIB_DIR)

clean:
	rm -f $(CODE)
	rm -rf $(LIB_DIR)

all: $(CODE) $(LIBS)



