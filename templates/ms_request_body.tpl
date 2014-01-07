<?xml version="1.0" encoding="UTF-16"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
	<s:Header>
		<h:cd xmlns:h="http://schemas.microsoft.com/windowsmetadata/services/2007/09/18/dms">
			<h:cv>6.1.7601</h:cv>
			<h:cc>en_US</h:cc>
		</h:cd>
	</s:Header>
	<s:Body>
		<DeviceMetadataBatchRequest xmlns="http://schemas.microsoft.com/windowsmetadata/services/2007/09/18/dms">
			<LocList>
				<loc>en-us</loc>
				<loc>en</loc>
			</LocList>
			<MIDRequests></MIDRequests>
			<HWIDRequests>
				<gdmdhwid>
					<rid>0</rid>
					<hwids>
						<hwid>DOID:USB\VID_{{ vid }}&amp;PID_{{ pid }}</hwid>
					</hwids>
				</gdmdhwid>
			</HWIDRequests>
		</DeviceMetadataBatchRequest>
	</s:Body>
</s:Envelope>