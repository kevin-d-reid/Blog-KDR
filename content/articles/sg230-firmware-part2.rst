==================================================================================
Modding a network appliance firmware for greater security Part 2: Firmware modules
==================================================================================

:date: 2024-02-11 09:15

:category: Hardware
:tags: Firewall, Homelab, Modding, Security
:author: Kevin D. Reid
:slug: modding-firewall-firmware-part2
:url: modding-firewall-firmware-part2
:status: published

Welcome back to part 2 of my foray into firmware modding! With our investigation concluded in part 1, we can dive into upgrading the firmware, starting with the different modules that it's composed of. Firmware modules are used to interface with and extend the functionality of hardware devices separate from the main firmware. Which modules will be used depends on whether UEFI boot or Legacy BIOS boot mode is selected, with UEFI using EFI and Legacy using OROM. We'll be tackling both EFI and OROM modules in this order; SATA, Network, and Video.

SATA EFI and OROM Modules
=========================

Tools: `UEFI BIOS Updater`_

.. _`UEFI BIOS Updater`: https://winraid.level1techs.com/t/tool-guide-news-uefi-bios-updater-ubu/30357

NOTE: Our SG230 uses Intel’s H110 chipset, which does not support hardware RAID. There’s no benefit to doing this section and it can be skipped, I only included it for completeness and to show the process.

This section only uses UBU, but will require some files to be added first. We’ll start with the `EFI module`_ by downloading the latest available for the 100/200 series chipset, EFI RaidDriver v15.9.3.3408. Remember that version number as we get the corresponding `OROM module`_. The version numbers don't need to match, but it's recommended to do so to maintain identical behaviour if switching between UEFI and Legacy boot.

.. _`EFI module`: https://winraid.level1techs.com/t/intel-efi-raid-vmd-bios-modules/23689
.. _`OROM module`: https://winraid.level1techs.com/t/ahci-raid-option-rom-modules/17526

Once you have acquired both ``RaidDriver.efi`` and ``RaidOrom.bin``, copy them to the UBU folder ``Files/intel/RST``. Start UBU and select the SATA menu, then press 1 to start the replacement. UBU will replace both modules automatically with no further work needed, it’s that easy!

.. image:: images/sg230-firmware/sata+network/ubu-sata-replace.png
	:alt: Replacement of the SATA modules using UEFI BIOS Updater


Networking
==========

Tools: MMTool_, UEFITool_, `UEFI BIOS Updater`_, SetDevID

.. _MMTool: https://www.mediafire.com/file/t5w592roapx6wzl/MMTool_Aptio_5.02.0024_Mod.7z/file
.. _UEFITool: https://github.com/LongSoft/UEFITool/releases/tag/0.28.0

If this were a straightforward replacement we would only use UBU like in part 1, but since the SG230 has the wrong modules installed we now need to manually replace the modules with the correct ones. Network modules are typically used for Wake-on-LAN and PXE boot, neither of which is typically needed for a firewall that will operate 24/7. Nevertheless, I wanted to give myself more of a challenge and provide the steps in case someone else has a similar issue.

OROM modules
------------

Our first section to target will be the OROM modules, and we’ll be using AMI’s Module Management Tool or MMTool. I opted for the modded version of v5.02.0024 linked above that works with both Aptio IV and Aptio V firmware. Start MMTool and select load image to load our firmware, changing the file type to all to see the .bin file. 

.. image:: images/sg230-firmware/sata+network/mmtool-start.png
	:alt: Initial screen for MMTool

Navigate to the Option ROM tab and select the ROM with DevID 155A. If you recall the initial UBU network upgrade from part 1, this incorrect DevID was associated with the Boot Agent GE. To retain the settings of the existing OROM, we’ll extract this OROM and change it’s DevID to the correct one, then reinsert it into our firmware file. Select the Extract an Option ROM radio button and Browse to set a filename, then hit Apply.

.. image:: images/sg230-firmware/sata+network/mmtool-extract-155a.png
	:alt: Extraction of Option ROM with Device ID 155A using MMTool

Since we can’t reuse the OROM for DevID 15B8, we’ll get a replacement from the UBU folder ``Files/intel/LAN/OROM``. Each of the LOM files in this folder has a corresponding text file that lists the compatible DevIDs. Both our I210 and I211 based network controllers are present in o1562GE.txt and OBAGE.txt, so you can choose either .LOM file as UBU will update it anyways.

NOTE: Originally, Boot Agent GE was the only OROM used. With versions after 1.5.62, Intel spun off certain adapters into the legacy Boot Agent CL, with modern adapters continuing to use GE. Since DevID 155A is supported by the legacy boot agent, UBU wouldn’t upgrade the Boot Agent GE past version 1.5.62 the first time to retain that DevID compatibility.

The OROM modules must first be modified before (re)insertion using SetDevID, which can be found within UBU’s main folder. Copy the SetDevID.exe and OROM files to another folder, then open a terminal in that location. You’ll need to run the command below twice; changing the desired DevID, source, and destination files for each network controller::

	SetDevID <DevID> <Source file> <Dest file>

.. image:: images/sg230-firmware/sata+network/setdevid-update-orom.png
	:alt: Setting correct Device ID for both extracted and new Option ROM

From here, we’ll launch MMTool and load our firmware, then select the Option ROM tab again. Select an incorrect DevID and it’s corresponding new OROM (remembering that 155A → 1539 and 15B8 → 1536) along with the Replace an Option ROM radio button, then hit Apply for each one.

.. image:: images/sg230-firmware/sata+network/mmtool-replace-orom.png
	:alt: MMTool Option ROM tab with both Option ROM replaced

EFI modules
-----------

For this section, we’ll have to rip the modules from another motherboard that has the I211-AT controller. I selected the ASRock X370 Gaming K4 which has a single I211 port, and downloaded the earliest firmware 2.20. We’ll need the older 0.28.0 version of UEFITool for the extraction as the newer NE releases can only read and extract.

With UEFITool open and the X370 firmware loaded, we’ll search for the text ``LANDxe`` and ``DriverI211``. Right-click the PE32 image section under each GUID and extract the body to another folder. From here, we’ll load our SG230 firmware with UEFITool and search for ``gigabitlan``, which gives us 2 GUIDs. Right-click the PE32 image section under each GUID and replace the body with the extracted equivalent from the X370 firmware (IntelLANDxe → IntelGigabitLanDxe, IntelLanUefiDriverI211 → IntelGigabitLan), then save the modified image. 

.. image:: images/sg230-firmware/sata+network/uefitool-replace-dxe.png
	:alt: Replacement of DXE module using UEFI Tool
.. image:: images/sg230-firmware/sata+network/uefitool-replace-driver-i211.png
	:alt: Replacement of main driver using UEFI Tool

Before we start UBU and replace our modules, we’ll also upgrade the EFI driver provided by UBU. Newer versions can be acquired from this Level1Techs `forum post`_, and through some trial and error, I found that PRO1000 versions from 9.7.xx onward would successfully update but fail to show up in UBU when reloaded. Therefore, I settled on 9.6.02 as the latest one fully compatible with the program. Download and extract the efi file, then move it to the UBU folder ``Files/intel/LAN/EFI`` and replace the existing ``PRO1000.efi`` file. With our EFI driver updated, start UBU and go to the network menu, then start the replacement. As UBU goes through the replacement, note the correct DevIDs for the OROM modules.

.. _`forum post`: https://winraid.level1techs.com/t/efi-lan-bios-intel-gopdriver-modules/33948

.. image:: images/sg230-firmware/sata+network/ubu-network-replace-correct.png
	:alt: Correct network modules applied with UEFI BIOS Updater


Video
=====

Tools: MMTool_, UEFITool_, `Swiss File Knife`_, `UEFI BIOS Updater`_, Intel BMP

.. _`Swiss File Knife`: http://stahlworks.com/dev/swiss-file-knife.html

There are 3 modules to be upgraded here; EFI GOP driver, GOP VBT, and VBIOS OROM. The EFI driver is fairly straightforward as UBU has both a compatible option that will be automatically applied and the latest which can be force-applied if the GOP VBT is the right version. On the other hand, the GOP VBT and OROM will need to have their settings extracted from the current modules and transplanted to the new ones. There’s also a couple caveats for what version our GOP VBT will be updated to.

.. image:: images/sg230-firmware/video/ubu-video-stock.png
	:alt: Stock video modules in UEFI BIOS Updater

VBIOS OROM
----------

Like the network section above, we’ll start off with the VBIOS OROM. Before we begin this section though, there’s a docx file that can be found in UBU’s download folder under ``Files_07072020/Intel_VBIOS_and_BSF_r3.7z`` that should be extracted and read first. With the file open, note the two asterisks at the bottom of the table. Our current OROM version is 1033, while 1034 and above support Kabylake. Alongside the microcode and ME region, updating the Video modules will be important for adding in Kabylake support too.

While we’re still in the extracted archive, copy the file ``SKL/1033/skl_1033.bsf`` and the folder ``SKLKBLCFLAML/1062`` to another working folder. As noted above, our current VBIOS version is 1033, so we’ll need the corresponding BSF file to transfer our settings out. The 1062 folder is our new clean VBIOS and BSF file. Version 1065 is also present in the table, but the crucial BSF file for transferring the settings is missing, leaving version 1062 as the latest available option with both required files.

Extraction of the VBIOS module is best done through MMTool, so start that and open the firmware file, then navigate to the Option ROM tab. The DevID for our VBIOS is 406, so select that and the Extract an Option ROM radio button, give the file an appropriate name like vbios_old.dat and apply to extract the OROM.

.. image:: images/sg230-firmware/video/mmtool-extract-vbios.png
	:alt: Extraction of the VBIOS Option ROM with MMTool

Next step will be to generate our settings transfer file, which requires the Intel Binary Modification Program, found under the download folder for UBU in the Tools folder. Download and extract the archive ``BMPv2_67PV_External.zip``, then install and launch the program. Click the folder icon in the top left then select our extracted VBIOS and its corresponding BSF file.

.. image:: images/sg230-firmware/video/bmp-old-vbios+bsf.png
	:alt: stock VBIOS plus BSF file to be opened with BMP

.. image:: images/sg230-firmware/video/bmp-main-old-vbios.png
	:alt: BMP main page with stock VBIOS

Navigate to BIOS Setting → Save All on the menu bar, and save the SSF file with a proper name like ``transfer.ssf``. There is one more thing that has to be done prior to application of our settings, so open your SSF file with a text editor like Notepad. CTRL+F and enter ``STRING $Signon``, note the build date of 2014/12/12, then delete that entire line. That line represents the name and version number of our old VBIOS, which we don’t want to carry over to the new.

Now that the transfer file is prepared, open up BMP again and load the new VBIOS and BSF file, then apply the ``transfer.ssf`` file from the menu BIOS Setting → Apply All. BMP will quickly scroll though and apply all the settings, but we’ll look around before we save and quit. On the main page, the VBIOS GOP version has gone from 200 to 209, and the platform now lists Skylake/Kabylake. The settings that will be applied from our old VBIOS are highlighted on the left, and if you drill down you’ll see the individual settings that were changed. 

.. image:: images/sg230-firmware/video/bmp-main-new-vbios.png
	:alt: BMP main page with updated VBIOS

NOTE: If you refer back to the docx file with the version table, you’ll see that the size on the right column increased from 3786 to 4252 bytes, meaning additional settings were added. These won’t show as changed in the sidebar, so loading the old and new VBIOS side-by-side and manually checking would be a good idea.

Most of our changes happened to the Panel Self Refresh wakeup timers. You’ll want to go through and check all 16, as the value for the wakeup timers changed from an integer value to a drop-down menu, meaning the old value didn’t carry over correctly. PSR isn’t too important here as our device will be operating headless most of the time, but I still went through and chose 2.5msec for each one as it’s closest to the original 5msec. Navigating back up to Legacy VBIOS Configuration → Sign-on Message Options, in the text box for ``Video BIOS signon message`` will show us the build date of 2018/12/09, nearly 4 years newer than the old one.

We’ll use UBU to replace the OROM, so save the file as ``vbiosskl.dat`` and move it to the UBU folder ``Files/intel/VBIOS``. Load up UBU and select the video section to see that our VBIOS is ready for insertion.

.. image:: images/sg230-firmware/video/ubu-video-vbios-ready.png
	:alt: UEFI BIOS Updater Video menu with updated VBIOS ready for insertion

GOP VBT and EFI driver
----------------------

For the GOP VBT, extract the archive ``Files_07072020/Intel_GOP_VBT_r4.7z`` from UBU’s download folder and open the docx file present within. This file lists the GOP VBT versions in the left column, with the center representing the GOP EFI driver that is likely to be most compatible. Our current GOP VBT v200 and EFI driver 9.0.1037 are perfectly matched with the BSF file present, but figuring out an upgrade path is a little more difficult.

If you refer back to UBU’s video screen, UBU will automatically update the EFI driver to one of 2 versions depending on the GOP VBT currently installed. For the most compatible version 9.0.1080, v212 is the best match, while the latest 9.0.1112 requires v228 or later. Reading through this thread_ (which also documents the process of transferring the settings), there are no major breaking changes updating to v221, but updating to v228 has some issues that have to be dealt with first. That’s why we’ll do an intermediate upgrade: from v200 to v221, then to v228.

.. _thread: https://winraid.level1techs.com/t/guide-transfer-of-specific-intel-orom-vbios-and-gop-vbt-settings-by-using-intel-bmp-tool/30930

Like the OROM section before, we’ll copy our current VBT BSF file and our desired upgrade version(s) to another folder. Start UEFITool and open up our firmware, then search for one of the following hex strings: 

	- 00F82456425420
	- 00F8........2456425420
	- 2456425420

Right-click the GUID and extract the body to get the file ``vbt_old.bin``, our current VBT. 

From here we can open BMP again and follow the same procedure done to the VBIOS: load our ``vbt_old.bin`` and it’s corresponding BSF file from the extracted archive ``SKL_KBL/200/vbt.bsf``, save the transfer settings to an SSF file called ``vbt200-221.ssf``, then load the VBT bin and BSF file for version 221 and apply all settings.

.. image:: images/sg230-firmware/video/bmp-main-vbt221.png
	:alt: BMP main page with GOP VBT 221

Looking over our applied settings, the changes are similar to VBIOS with PSR making up most of it. Like before, set each PSR wakeup timer to a valid value. You’ll also notice that there was no need to remove the string from the transfer file, that version indicator isn’t present in the GOP VBT. Save the VBT with file name ``vbtskl.bin``, then move it to the UBU folder ``Files/intel/GOP_VBT``. Load up UBU and you’ll see the VBT file ready for insertion under the video section.

.. image:: images/sg230-firmware/video/ubu-video-vbios+vbt221.png
	:alt: UEFI BIOS Updater Video menu with GOP VBT 221 ready for insertion

With our EFI and OROM modules now updated and supporting Kabylake, we can optionally update the GOP VBT to v228 to match the latest EFI driver 9.0.1112. The structure of VBT v228 changed compared to earlier versions, leading to error messages if you try to apply your current SSF file to it.

.. image:: images/sg230-firmware/video/bmp-error-log-228.png
	:alt: BMP error log when updating to GOP VBT 228

Luckily, in the `same thread`_ we referred to earlier, one of the contributors made a batch script that updates the SSF file automatically. This will require installation of the Swiss File Knife or SFK. Repeat the SSF transfer file creation above to make a fresh SSF file from our VBT221 with the PSR changes, then move that file and the batch script to SFK’s tools directory and launch it from the command line::

	Vbt221to228.bat <your SSF file>

.. _`same thread`: https://winraid.level1techs.com/t/guide-transfer-of-specific-intel-orom-vbios-and-gop-vbt-settings-by-using-intel-bmp-tool/30930/347

.. image:: images/sg230-firmware/video/sfk-vbt221-to-228-script.png
	:alt: Command line output from GOP VBT update script from 221 to 228

Load VBT228 and its BSF file in BMP then apply the updated SSF file. There should be no error log this time, and the only changes made are to the data link training for eDP, which changed from a drop-down to an integer value. The integer value matches the previous drop-down already, so no changes are needed here. Save the VBT file and move it to the appropriate UBU folder, renaming it if necessary, then launch UBU and apply each video module while using the force option for the EFI driver.

.. image:: images/sg230-firmware/video/ubu-video-replace.png
	:alt: UEFI BIOS Updater Video menu with all video modules updated

Firmware modules summary
========================

That concludes our work with the firmware modules. We learned a few different methods to swap out and upgrade various modules, and even upgraded a critical piece for potential Kabylake support. The last part of this series will dive into CPU microcode and the Intel Management Engine, along with modding the BIOS menu and hardware upgrades. Thanks for reading!
