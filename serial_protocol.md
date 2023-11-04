# USB Communication Protocol

## Handshake procedure

In a fresh installation, unless a specific COM port has been specified, the host has no information about the device other than the VID, PID and serial number. Normally that would be enough to identify a device but because we're using a Pi Pico running MicroPython, we are stuck with its PID and VID (11914 and 5 respectively) which are common to all Picos. The serial number _is_ unique but we have no good way of knowing this in advance without finding it from device manager and manually entering it, which is not much better than manually specifying a COM port.

We could of course design all Pico projects to accept the same incoming message format as part of a common handshake procedure - however, while this would work for completed projects, it would likely interfere with the REPL for any Pico being used for development.

To avoid this problem, we instead have the device broadcast an identifier unique to the volume knob project and the host listens for that message to determine which COM port it is connected to:

1. Device boots into startup state and begins broadcasting its ID
2. Host program starts up and begins listening for ID messages from all COM ports matching VID and PID
3. Host program receives ID message and establishes connection with the device

## Disconnect Handling

The above procedure works fine as long as the device knows it has not yet established connection with the host software, as is the case on startup. In addition, the host software can send a restart message to return the device to this state upon exit. However, in the event that the host software exits unexpectedly*, or if the connected PC goes to sleep, the device has no way of knowing it is no longer connected.

To get around this problem, there are two possible strategies:

- When idle, the host software sends a ping message every few seconds to tell the device it is still there. If the device stops receiving these, it knows it has disconnected and can return to broadcast mode.
- After the COM port has been identified for the first time, it is saved to a cache file and read on subsequent startups to bypass the device discovery procedure. We can also cache the serial number so that we can verify the device's identity in future, since the serial number cannot change - this is useful if for some reason the COM port changes (it is possible to manually reassign them)

I have opted for the second strategy as it requires no additional messages, and importantly it works regardless of what state the device is in, so is generally more robust.

_\* Although we can catch most errors and exit cleanly, it is always possible that an error occured in the serial connection itself, which would make this impossible._

## Core Message Protocol

During normal operation, messages sent between the host and device consist of a single ID byte followed by the message payload.  Two different approaches were considered for determining when to stop reading a message:

1. Send a newline char (\n) at the end of each message and use readline() - neat but inefficient  
   \+ Simple to implement  
   \+ No need to know the size of messages beforehand  
   \- Adds 1 byte to every single message  
2. Define the length of each message at compile-time, then look that up once message type has been determined and
   read the rest of the message based on that - messier but efficient  
   \+ No additional bytes need to be sent  
   \- More complex to implement, requires some back-and-forth between serial managers and message_protocol  

Since all messages are of known length, option 2 was chosen for its better efficiency.

The protocol itself does not specify the direction a message is to be sent; this distinction is made only by the existence or absence of a handler function for a particular message type on either side. As such, message IDs are universal; both directions share the same set of IDs. A single message type may be sent in both directions so long as a handler is present on both sides; `VolumeMessage` does exactly this. The intended direction of each message is, however, captured in documentation for reference purposes.

Practically, this system is implemented using an object-based system, with a base `Message` class that handles the ID byte and exposes template encode/decode methods (`to_bytes()` and `from_bytes()` respectively) for implementation by concrete message classes.

Instantiation of incoming messages and dispatch of outgoing messages are handled by the serial manager classes. These are singletons that extend a common base class, allowing most of the send/receive code to be centralised, with only the actual read/write methods being different on either side due to framework differences. Importantly, the read method is required to be non-blocking so that it can be polled during the program update cycle. Any number of messages may be received during a single serial manager update; the buffer will always be read until it is empty.

Both the message protocol and the base serial manager class are common, meaning they are present in both the host and device code. This is a benefit of using Python for both sides, which both reduces the amount of code required and guarantees that both programs interpret messages in the same way.

_See [`message_protocol.py`](), [`serial_manager.py`]() and its subclasses for the full implementation._

> It may seem a bit overkill to give each message type its own class, as it does result in a fair amount of boilerplate. The most viable alternative would be to use a proxy pattern with network handler classes for both device and host that inherit from a common base class, with functions for each type of message. This achieves the same goal of providing a contract for exactly what data goes into each type of message. However, the issue with this approach is that we don't necessarily know the type of an incoming message (sometimes it can be inferred from context but on the host end especially, it could be anything). This means we would have to have a single centralised decode() function anyway, and then a switch statement for each kind of message (potentially broken out into other functions). This would then have to return a tuple of values including the ID so that the caller can then determine the type of message... all of which points to objects being a better solution.