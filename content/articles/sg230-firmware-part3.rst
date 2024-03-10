==========================================================================================
Modding a network appliance firmware for greater security Part 3: Microcode, ME, and more!
==========================================================================================
:date: 2024-02-25 17:14
:category: Hardware
:tags: Firewall, Homelab, Modding, Security
:author: Kevin D. Reid
:slug: modding-firewall-firmware-part3
:url: modding-firewall-firmware-part3
:status: published

Welcome to the third and final part of my firmware modding series! Now that the various firmware modules are fully updated, we can turn our attention to the two major security issues remaining; microcode and Management Engine. Microcode is the translation layer between CPU instructions and low-level operations, essentially firmware specifically for the CPU. Intel's Management Engine is a separate subsystem on the chipset that handles things like boot-time security and remote out-of-band management. Finally, we'll modify the BIOS menus and flash the firmware back onto the device, testing for Kabylake support too.

CPU Microcode
=============
Tools: MMTool_, MCExtractor_

For the microcode, we’ll need the microcode files themselves to insert into the firmware, which can be found at this `Github repo`_. Navigate to the Intel folder then CTRL+F to find the files by their CPUIDs; 506E3 for Skylake, 906E9 for Kabylake. At time of writing, this gives us patches 0xF2 for Skylake and 0xF4 for Kabylake, both last updated in early 2023.

To insert these new microcode files, start MMTool and load our firmware file, then switch to the CPU Patch tab. Select the patch 0x8A and the Delete Patch Data radio button, then hit Apply to remove it from the file. Browse to the new microcode files and select the Insert Patch Data radio button, then hit Apply again to add them to the firmware file. Your finished result should have 2 files listed; 1 for CPUID 906E9 with revision 0xF4, and 1 for CPUID 506E3 with revision 0xF2.

.. image:: images/sg230-firmware-part3/mmtool-microcode-updated.png
	:alt: MMTool CPU Patch tab with Skylake and Kabylake microcode present

Save the firmware file and quit MMTool. We can also open MCExtractor to verify both microcode files are present.

.. image:: images/sg230-firmware-part3/mcextractor-updated.png
	:alt: MCExtractor with Skylake and Kabylake microcode present

Management Engine
=================
Tools: MEAnalyzer_, `Intel FIT`_, MEInfo

Before we can start upgrading the Management Engine, we have to determine which version to upgrade to. As we found out at the end of part 1 in this series, our ME version is currently 11.0.0.1191. This Level1Techs `forum post`_ details the upgrade instructions for the 11.x branch, and specifies that the major and minor numbers must match, in this case 11.0. However, referring back to the Intel `SA-00086`_ advisory shows that to protect against those CVEs, a minimum version of 11.8.50.3425 must be installed. Therefore, we'll go ahead with using the 11.8 branch.

The ME firmware can be acquired from this `MEGA archive`_ which posts the latest available. We want the Corporate H SKU to match our current firmware, which gives us the file ``11.8.95.4551_COR_H_DA_PRD_RGN.rar``. We can verify it is compatible by extracting and loading the ME firmware in MEAnalyzer.

.. image:: images/sg230-firmware-part3/meanalyzer-new-meregion.png
	:alt: MEAnalzyer with new Management Engine region loaded

Comparing the image above to our current firmware, we can see that both are for the Corporate H SKU and support the 100-series Sunrise Point or SPT-H D chipset. Kabylake support is added with the chipset KBP-H A, along with two others in the same family. The date it was built is 2023-05-24, over 7 years newer. One major section we need to pay attention to is ``File System State``, which is ``Unconfigured`` currently. Our current firmware has the state ``Initialized``, which means it was extracted from an online device and is "dirty". To have a clean flash performed without corrupting the ME region, the state must be ``Configured`` with the settings of the system.

To begin upgrading this section, we'll first need to extract the settings for our current ME using the Intel Flash Image Tool or FIT from the link above. Download the archive for CSME 11 and extract it, then execute the program at ``Flash Image Tool/WIN32/fit.exe``. With FIT launched, go to File → Open and select the modded firmware file, then go to Build → Build Settings and select the ``No`` option for Generate Intermediate Files. From here, we'll save the config as an XML file to be reapplied later, then quit FIT.

.. image:: images/sg230-firmware-part3/fit-stock-me.png
	:alt: Intel FIT with firmware loaded

Within FIT's main folder, there will be a subfolder with the name of the modded firmware file. Enter it and the subfolder within to see the different regions of the firmware split into separate .bin files. We'll want to replace the ``ME Region.bin`` file with the ME firmware file downloaded from the MEGA archive above, renaming it to the same filename so FIT recognizes it.

Launch FIT again, then load the ``config.xml`` file made earlier. From here, we'll select Build → Build Image to rebuild our modded firmware, the file now present in FIT's folder as ``outimage.bin``. We can load this with MEAnalyzer to verify that the status is correct for a clean flash.

.. image:: images/sg230-firmware-part3/meanalyzer-me-upgraded.png
	:alt: MEAnalyzer with modded firmware open showing upgraded Management Engine region

During the build, I received a warning about Boot Guard being disabled. After some further research I found that it's normal and to do with hardware fuses on the chipset. We can optionally check this with MEInfo, which was also downloaded in the same CSME 11 archive. The DLL files in the WIN64/WIN32 folders are corrupted in the CSME 11 archive, so I lifted working ones from CSME 12 instead. MEInfo is launched with the ``-verbose`` flag from the command line, which gives a lot of info about the Management Engine including what features are supported/enabled and which fuses are set. In Boot Guard's case, those fuses are ``Measured Boot`` and ``Verified Boot``. If either fuse was set, some or all regions of the firmware would not be able to be modified, and this entire series might not have happened in the first place. 

.. image:: images/sg230-firmware-part3/meinfo-fpf.png
	:alt: Last section of MEInfo showing which fuses are set

BIOS menu modifying
===================
Tools: AMIBCP_, `UEFI BIOS Updater`_ for verification

This last modding section is more of a bonus. When we flash this firmware back onto the device, the build date and version will be identical to the stock BIOS. With the American Megatrends BIOS Configuration Program or AMIBCP for short, we can modify the info and menus displayed in the BIOS. Start by downloading the program above and launching it, then loading our firmware.

.. image:: images/sg230-firmware-part3/amibcp-start.png
	:alt: AMIBCP with the modded firmware loaded

For changing the version and build date, the two latter tabs ``DMI Tables`` and ``BIOS Features`` have strings that can be replaced. I used the current date as the build date and 1.10 as the version number to make modded builds easy to identify.

The menus that are visible are configured on the ``Setup Configuration`` tab. If you drill down into the folders, you can see that they align with the different tabs and settings within the BIOS. Most of them are marked ``Yes`` for showing and ``Default`` for access use. To change any setting in this section, access use must be set to ``USER`` for that setting as well as all parent folders. For my options, I hid the core version and project version on the BIOS Main page and the L4 cache line under CPU configuration by changing show to ``No`` and ``USER`` for the access use all the way up to the root folder. I may go further with this in the future, but just updating the info and removing excess clutter is good enough for now.

We can also use UEFI BIOS Updater to verify the version and build date updated successfully. Save and quit AMIBCP, then load up UBU with the modded firmware and watch for the updated info as the modules load in.

.. image:: images/sg230-firmware-part3/ubu-version-edited.png
	:alt: UEFI BIOS Updater loading screen showing edited BIOS version

Flashing the firmware
=====================

With that, our firmware modding is finished! All that's left now is to flash it back onto the device. Load up a Linux live environment again and move the firmware file into the home folder, then execute the command::

	sudo flashrom -p internal -w SG230r2_BIOS1.10.bin

This command is nearly identical to the one used for extraction in part 1, the only difference being swapping the ``-r`` read flag for a ``-w`` write flag. The flash will take a bit of time, but once it finishes the final line will display ``VERIFIED`` if successful.

.. image:: images/sg230-firmware-part3/flashrom-write.png
	:alt: Successful flash of firmware using Flashrom

Now that the firmware is flashed, initiate a reboot from the live environment. The device will take some time before it shuts down gracefully, and once it does the device may try to boot with the fans ramped up to full speed. If this happens and the device doesn't boot after a short while, cut power and try starting it again. A successful flash will have you back at the BIOS POST within no more than 2 restarts.

There is one more step that has to be done when the firmware has an upgraded Management Engine. You'll need a drive with Windows installed on it, along with the Flash Programming Tool found in the Intel CSME download from the ME section above. With the SG230 running Windows, run this command and wait for the device to restart::

	fptw64.exe -greset
	
This will reinitialize the ME co-processor and have it properly accept the modified firmware image. 

Recovering from a failed flash
------------------------------

When flashing the firmware back onto your device, there's always the possibility that the flash can fail. Either the flashing process was interrupted or a setting in the firmware was changed that prevented the newly-flashed device from booting successfully. Your device is effectively a brick at this point, but not all hope is lost.

To recover from a failed flash, you'll need an external SPI programmer. The most common one around is the CH341A Mini Programmer, which can be found for $5 to $15 CAD on sites like Ebay and Aliexpress. Make sure to get one that has the right accessories, at minimum an SOIC8 clip and adapter for soldered flash chips. You'll also need a known good firmware for your device. This can be a backup of the stock firmware or a fresh download from the manufacturer's website.

Preparing for a firmware flash is done by unplugging and opening up the SG230, removing the 4 screws around the top cover then sliding it back. Our firmware chip is located towards the front of the board, identified by it's small size and 2x4 arrangement of pins, a Winbond 25Q128FV. With our CH341A, we'll insert an adapter for the SOIC8 clip into the 25XX marked section, keeping pin 1 on the adapter PCB towards the back, away from the USB connection. Next we'll insert the SOIC8 clip plug end, again making sure that the red wire on the ribbon cable connects to pin 1 on the adapter.

.. image:: images/sg230-firmware-part3/ch341a.jpg
	:alt: CH341A connected to laptop and SG230 flash chip

To start recovery, plug the USB end of the CH341A into a computer that has Flashrom installed. The SOIC8 clip will attach directly to the firmware chip, connecting pin 1 on the ribbon cable to pin 1 marked on the chip, usually a dot but sometimes a notch at one end. To verify things are connected properly, run a read command in Flashrom to read back the existing firmware::

	sudo flashrom --programmer ch341a_spi -r backup.bin

The firmware may fail to read the first time, so try readjusting the clip until you get a successful read. Once it succeeds, write the replacement firmware with this command::

	sudo flashrom --programmer ch341a_spi -w newbios.bin

Once the new firmware is flashed successfully, remove the SOIC8 clip from the motherboard. Reset the CMOS via a jumper if available or remove the battery and turn the SG230 on for a few seconds to reset the BIOS. With the battery reinserted and cover put back on, the SG230 should boot successfully into the BIOS with default settings applied.

Verifying changes
=================
Now that our new firmware is successfully flashed, we'll poke around in the BIOS to see what has changed, starting with the main menu.

.. image:: images/sg230-firmware-part3/bios-main-upgraded.jpg
	:alt: BIOS main page with settings changed
	
On the boot POST screen, I did see both the updated and the old build date and version. The main menu still shows the old version and date, so it seems there's one other section where that data is that we missed. The core and project version lines are missing, matching what was removed in AMIBCP.

.. image:: images/sg230-firmware-part3/bios-cpu-upgraded.jpg
	:alt: BIOS CPU page with upgraded microcode and L4 cache line removed
	
Moving along to the CPU page, our G4400 CPU now has the latest microcode patch F2. The L4 cache line is also missing.

.. image:: images/sg230-firmware-part3/bios-net-boot-upgraded.jpg
	:alt: BIOS boot page with OROM version upgraded
	
Rebooting to Legacy boot mode with Network OROM loaded and going to the boot tab, our OROM version for PXE boot is upgraded to v1.5.89. The menu to configure the OROM by pressing CTRL+S is no longer available, but there wasn't really anything to configure on the old version either, and since we're not likely to use this feature it's an acceptable tradeoff.

Finally, we can boot into a Windows drive and run some tests to check that we're sufficiently protected from CVEs. We'll start with the `InSpectre test`_, which checks whether a system is vulnerable to the Spectre and Meltdown CVEs.

.. image:: images/sg230-firmware-part3/inspectre-results.png
	:alt: InSpectre results, system is fully patched and not vulnerable
	
As shown above, our firewall is fully patched against the CVEs. With the latest microcode now being used, we're also protected against the variety of CVEs that came after Spectre/Meltdown too.
	
For the ME Region, we'll use Intel's `SA-00086 vulnerability test`_ to check that our firmware has been patched against those CVEs. As shown in the image below, our firmware is fully patched not only against SA-00086 CVEs but many of the subsequent CVEs that came after.

.. image:: images/sg230-firmware-part3/csme-results.png
	:alt: SA-00086 results, system is fully patched and not vulnerable

Kabylake support?
-----------------
Now that we've verified that our system is fully patched, we can try inserting a Kabylake CPU to test if our firewall now supports it. I pulled an i7-7700T from a virtualization host, opened up the SG230, and swapped the CPUs.

Unfortunately, even with all the different sections upgraded, the SG230 failed to boot with a Kabylake CPU. There's something else in the firmware that is preventing it from full support. Luckily, the differences between Skylake and Kabylake are fairly minor, just increased clock speeds and slightly faster memory for the latter, so I'm okay with leaving it alone for now.

Hardware upgrades
=================
Improving the security of our firewall isn't enough, I also looked into upping it's capabilities with hardware upgrades. I doubled the RAM and SSD capacity to 16GB and 240GB respectively with spare parts I had lying around, and ordered an Intel i3-6300T CPU to round things out. These upgrades are fairly balanced, and bring CPU power closer to the next firewall in the lineup, the SG310r2. The top CPU option would be the i7-6700, but that's getting into overkill levels of processing power. For expanding network ports, used expansion cards with 4x10 gigabit SFP+ run about $225 CAD if you seek out Checkpoint-branded modules.

Conclusion
==========
And that rounds out this 3 part series. We've covered a lot of ground and greatly improved the security of our firewall firmware. I have far greater confidence in deploying it to my network perimeter, and saved it from being scrapped early. Hopefully you learned a lot and didn't end up accidentally bricking your board like I did! Thanks for reading!


.. _MMTool: https://www.mediafire.com/file/t5w592roapx6wzl/MMTool_Aptio_5.02.0024_Mod.7z/file
.. _MCExtractor: https://github.com/platomav/MCExtractor
.. _`Github repo`: https://github.com/platomav/CPUMicrocodes
.. _MEAnalyzer: https://github.com/platomav/MEAnalyzer
.. _`Intel FIT`: https://mega.nz/folder/qdVAyDSB#FLCPaDVIsPYiy2TAUjD7RQ
.. _`forum post`: https://winraid.level1techs.com/t/guide-clean-dumped-intel-engine-cs-me-cs-txe-regions-with-data-initialization/31277/2
.. _`SA-00086`: https://www.intel.com/content/www/us/en/security-center/advisory/intel-sa-00086.html
.. _`MEGA archive`: https://mega.nz/folder/2Q0klQpA#6o04nlV_4xqfx76tjvgi4g
.. _AMIBCP: https://bittention.com/programs/amibcp/
.. _`UEFI BIOS Updater`: https://winraid.level1techs.com/t/tool-guide-news-uefi-bios-updater-ubu/30357

.. _`InSpectre test`: https://www.grc.com/inspectre.htm
.. _`SA-00086 vulnerability test`: https://www.intel.com/content/www/us/en/download/19392/28632/intel-converged-security-and-management-engine-version-detection-tool-intel-csmevdt.html?v=t
