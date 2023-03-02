.DEFAULT_GOAL := all

TARGET_DIR=/Volumes/CIRCUITPY
LIB_DIR=$(TARGET_DIR)/lib

CODE=$(addprefix $(TARGET_DIR)/, code.py secrets.py)
LIBS=$(addprefix $(LIB_DIR)/, adafruit_esp32spi adafruit_requests.mpy)

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



