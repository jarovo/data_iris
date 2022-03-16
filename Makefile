


LINUX_DIR_PATH = /lib/modules/$(shell uname -r)/build
INSTALL = install
PWD = $(shell pwd)
WORK = overlays
DTS_DEST_DIR = /opt/unipi/os-configurator/overlays
LIB_DEST_DIR = /opt/unipi/os-configurator
DESCRIPTION = description.yaml

#DTC_FLAGS_unipi-iris-unispi-slot12 := -@
templates =  $(wildcard *.template)
dtsi = $(wildcard *.dtsi)

#all: $(dtsi) $(templates) $(WORK)/imx8mm-pinfunc.h

all: $(WORK)/imx8mm-pinfunc.h libunipidata.so
	@#cp *.dtsi $(WORK)
	MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C $(LINUX_DIR_PATH) M=$(PWD)/$(WORK)

$(WORK)/imx8mm-pinfunc.h:
	@mkdir -p $(WORK)
	@ln -s $(LINUX_DIR_PATH)/arch/arm64/boot/dts/freescale/imx8mm-pinfunc.h $@

$(WORK)/Makefile: $(templates) $(DESCRIPTION)
	@python3 render-slot.py $(DESCRIPTION) -t template -o $(WORK)

unipi-values.c: template/unipi-values.template.c $(DESCRIPTION)
	@python3 render-slot.py $(DESCRIPTION) -t template -o $(WORK)

unipi-values.o: unipi-values.c
	gcc $^ -c -I unipi-hardware-id/include/ -fPIC

libunipidata.so: unipi-values.o
	gcc $^ -shared -o $@

install: $(wildcard $(WORK)/*.dtb)
	mkdir -p $(DESTDIR)/$(DTS_DEST_DIR)
	$(INSTALL) -m 644 $^ $(DESTDIR)/$(DTS_DEST_DIR)
	$(INSTALL) -m 644 libunipidata.so $(DESTDIR)/$(LIB_DEST_DIR)

clean:
	@touch $(WORK)/Makefile && MAKEFLAGS="$(MAKEFLAGS)" $(MAKE) -C $(LINUX_DIR_PATH) M=$(PWD)/$(WORK) clean
	@rm -f $(WORK)/*.dts
	@rm -f $(WORK)/Makefile
	@rm -f $(WORK)/imx8mm-pinfunc.h
	@rm -f libunipidata.so unipi-values.c unipi-values.o
