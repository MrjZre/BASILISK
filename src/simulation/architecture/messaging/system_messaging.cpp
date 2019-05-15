/*
 ISC License

 Copyright (c) 2016, Autonomous Vehicle Systems Lab, University of Colorado at Boulder

 Permission to use, copy, modify, and/or distribute this software for any
 purpose with or without fee is hereby granted, provided that the above
 copyright notice and this permission notice appear in all copies.

 THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

 */

#include "architecture/messaging/system_messaging.h"
#include <cstring>
#include <string>
#include <iostream>
#include "utilities/bsk_Print.h"

/*!
 * This constructor for TheInstance just sets it NULL
 */
SystemMessaging* SystemMessaging::TheInstance = NULL;

/*!
 * This constructor for SystemMessaging initializes things
 */
SystemMessaging :: SystemMessaging()
{
    this->messageStorage = NULL;
    this->CreateFails = 0;
    this->WriteFails = 0;
    this->ReadFails = 0;
    this->nextModuleID = 0;
}

/*!
 * This destructor for SystemMessaging sets the messageStorage spce to NULL.
 */
SystemMessaging::~SystemMessaging()
{
    this->messageStorage = NULL;
}

/*!
 * This gives a pointer to the messaging system to whoever asks for it.
 * @return SystemMessaging* TheInstance
 */
SystemMessaging* SystemMessaging::GetInstance()
{
    if(TheInstance == NULL)
    {
        TheInstance = new SystemMessaging();
    }
    return(TheInstance);
}

/*!
 *
 * @return uint64_t bufferCount
 * @param std::string bufferName
 */
uint64_t SystemMessaging::AttachStorageBucket(std::string bufferName)
{
    uint64_t bufferCount;
    MessageStorageContainer *newContainer = new MessageStorageContainer();
    newContainer->messageStorage.IncreaseStorage(sizeof(uint64_t)+20000);
    this->dataBuffers.push_back(newContainer);
    bufferCount = this->dataBuffers.size() - 1;
    newContainer->bufferName = bufferName;
    this->messageStorage = *(this->dataBuffers.end()-1);
    this->SetNumMessages(0);
    return(bufferCount);
}
/*! This method selects which message buffer is being read from when
 * messageStorage is referenced
 * @return void
 * @param uint64_t bufferUse
 */
void SystemMessaging::selectMessageBuffer(uint64_t bufferUse)
{
    std::vector<MessageStorageContainer*>::iterator it;
    it = this->dataBuffers.begin();

    if(bufferUse >= this->dataBuffers.size())
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"You've attempted to access a message buffer that does not exist. Yikes.\n");
        this->messageStorage = *this->dataBuffers.begin();
        return;
    }
    it += bufferUse;
    this->messageStorage = (*it);
}

/*!
 * This method records the current number of messages in the messageStorage space
 * @return void
 * @param uint64_t MessageCount
 */
void SystemMessaging::SetNumMessages(uint64_t MessageCount)
{
    if(this->messageStorage == NULL)
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"Received a request to set num messages for a NULL buffer.\n");
        return;
    }
    memcpy(&(this->messageStorage->messageStorage.StorageBuffer[0]), &MessageCount, sizeof(uint64_t));
}

/*!
 * This method sets all bits in messageSpace for the current buffer to 0
 * @return void
 */
void SystemMessaging::ClearMessageBuffer()
{
    memset(&(this->messageStorage->messageStorage.StorageBuffer[0]), 0x0,
           this->messageStorage->messageStorage.GetCurrentSize());
    this->SetNumMessages(0);
}

/*!
 * This method clears all data from all message buffers
 * @return void
 */
void SystemMessaging::clearMessaging()
{
    std::vector<MessageStorageContainer *>::iterator it;
    for(it=this->dataBuffers.begin(); it != this->dataBuffers.end(); it++)
    {
        delete (*it);
    }
    this->dataBuffers.clear();
    this->nextModuleID = 0;
    this->CreateFails = 0;
    this->WriteFails = 0;
    this->ReadFails = 0;
    this->messageStorage = NULL;
}

/*! This method gets the number of messages in the selected or requested buffer
 *
 * @param int32_t bufferSelect
 * @return uint64_t CurrentMessageCount
 */
uint64_t SystemMessaging::GetMessageCount(int32_t bufferSelect)
{
    uint64_t *CurrentMessageCount;
    if(bufferSelect < 0)
    {
       CurrentMessageCount = reinterpret_cast<uint64_t*>
           (&this->messageStorage->messageStorage.StorageBuffer[0]);
    }
    else
    {
        std::vector<MessageStorageContainer *>::iterator it;
        it = this->dataBuffers.begin();
        it += bufferSelect;
        CurrentMessageCount = reinterpret_cast<uint64_t*>
        (&((*it)->messageStorage.StorageBuffer[0]));
    }
    return(*CurrentMessageCount);
}

/*! This method returns total size of message buffer in bytes including:
 *  - a uint64_t for num msgs
 *  - a MessageHeaderData Struct for each message
 *  - (the size of a message + a single message header) * the number of buffers for that message
 * @return void
 */
uint64_t SystemMessaging::GetCurrentSize()
{
    uint64_t TotalBufferSize = sizeof(uint64_t); // -- The num-messages count;
    MessageHeaderData *MessHeader = reinterpret_cast<MessageHeaderData *>
    (&this->messageStorage->messageStorage.StorageBuffer[sizeof(uint64_t)]);
    uint64_t TotalMessageCount = this->GetMessageCount();
    uint64_t SingleHeaderSize = sizeof(SingleMessageHeader);
    for(uint64_t i=0; i<TotalMessageCount; i++)
    {
        TotalBufferSize += sizeof(MessageHeaderData);
        TotalBufferSize += MessHeader->MaxNumberBuffers *
        (MessHeader->MaxMessageSize + SingleHeaderSize);
        if(i < TotalMessageCount - 1)
        {
            MessHeader++;
        }
    }
    return(TotalBufferSize);
}

/*!
 * This method creates a new message within the currently selected buffer.
 * @param std::string MessageName The name of the message
 * @param uint64_t MaxSize The size of the message
 * @param uint64_t NumMessageBuffers The number of buffers to create for the message
 * @param std::string messageStruct The name of the struct
 * @param int64_t moduleID The id of the requesting module
 * @return uint64_t (GetMessageCount - 1), the assigned message ID
 */
int64_t SystemMessaging::CreateNewMessage(std::string MessageName,
    uint64_t MaxSize, uint64_t NumMessageBuffers, std::string messageStruct,
    int64_t moduleID)
{
    if (this->FindMessageID(MessageName) >= 0)
    {
        BSK_PRINT_BRIEF(MSG_INFORMATION,"The message %s was created more than once.\n", MessageName.c_str());
        if(moduleID >= 0)
        {
            std::vector<AllowAccessData>::iterator it;
            it = this->messageStorage->pubData.begin();
            it += this->FindMessageID(MessageName);
            it->accessList.insert(moduleID);
            it->publishedHere = true;
        }
    	return(this->FindMessageID(MessageName));
    }
    if(MessageName == "")
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"Module ID: %lld tried to create a message without a name.  Please try again.\n", moduleID);
        this->CreateFails++;
        return(-1);
    }
    if(NumMessageBuffers <= 0)
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"I can't create a message with zero buffers.  I refuse.\n");
        this->CreateFails++;
        return(-1);
    }
    if(NumMessageBuffers == 1)
    {
        BSK_PRINT_BRIEF(MSG_WARNING,"You created a message with only one buffer. This might compromise the message integrity. Watch out.\n");
    }
    uint64_t InitSize = this->GetCurrentSize();
    uint64_t StorageRequired = InitSize + sizeof(MessageHeaderData) +
    (MaxSize+sizeof(MessageHeaderData))*NumMessageBuffers;
    this->messageStorage->messageStorage.IncreaseStorage(StorageRequired);
    uint8_t *MessagingStart = &(this->messageStorage->messageStorage.StorageBuffer[this->GetMessageCount()*
                                                              sizeof(MessageHeaderData) + sizeof(uint64_t)]);
    if(this->GetMessageCount() > 0)
    {
        // leave the MessageHeaderData structs where they are but shift the
        // message data to make room for a new MessageHeaderData
        uint8_t *NewMessagingStart = MessagingStart + sizeof(MessageHeaderData);
        memmove(NewMessagingStart, MessagingStart, InitSize -
                this->GetMessageCount()*sizeof(MessageHeaderData));
        memset(MessagingStart, 0x0, sizeof(MessageHeaderData));
        for(uint32_t i=0; i<this->GetMessageCount(); i++)
        {
            MessageHeaderData *UpdateHeader = this->FindMsgHeader(i);
            UpdateHeader->StartingOffset += sizeof(MessageHeaderData);
        }
    }
    // check the length of the message name
    MessageHeaderData* NewHeader = reinterpret_cast<MessageHeaderData *>
    (MessagingStart);
    uint32_t NameLength = (uint32_t)MessageName.size();
    if(NameLength > MAX_MESSAGE_SIZE)
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"Your name length for: %s. is too long, truncating name\n", MessageName.c_str());
        this->CreateFails++;
        NameLength = MAX_MESSAGE_SIZE;
    }
    // check the length of the name of the struct
    strncpy(NewHeader->MessageName, MessageName.c_str(), NameLength);
    NameLength = (uint32_t)messageStruct.size();
    if(NameLength > MAX_MESSAGE_SIZE)
    {
        BSK_PRINT_BRIEF(MSG_ERROR,"Your struct name length for: %s. is too long, truncating name\n", messageStruct.c_str());
        this->CreateFails++;
        NameLength = MAX_MESSAGE_SIZE;
    }
    // fill in the data for the new header
    strncpy(NewHeader->messageStruct, messageStruct.c_str(), NameLength);
    NewHeader->UpdateCounter = 0;
    NewHeader->CurrentReadBuffer = 0;
    NewHeader->MaxNumberBuffers = (uint32_t)NumMessageBuffers;
    NewHeader->MaxMessageSize = MaxSize;
    NewHeader->CurrentReadSize = 0;
    NewHeader->CurrentReadTime = 0;
    NewHeader->previousPublisher = -1;
    NewHeader->StartingOffset = InitSize + sizeof(MessageHeaderData);
    //
    memset(&(this->messageStorage->messageStorage.StorageBuffer[NewHeader->StartingOffset]), 0x0,
           NumMessageBuffers*(MaxSize + sizeof(SingleMessageHeader)));
    this->SetNumMessages(this->GetMessageCount() + 1);
    AllowAccessData dataList;
    MessageExchangeData exList;
    dataList.publishedHere = false;
    this->messageStorage->subData.push_back(dataList); //!< No subscribers yet
    if(moduleID >= 0)
    {
        dataList.accessList.insert(moduleID);
        dataList.publishedHere = true;
    }
    this->messageStorage->pubData.push_back(dataList);
    this->messageStorage->exchangeData.push_back(exList);
    return(this->GetMessageCount() - 1);
}

/*!
 * This method subscribes a module to a message (but what does that mean different than read rights?)
 * @param std::string messageName name of the message to sub to
 * @param uint64_t messageSize size in bytes of message
 * @param int64_t moduleID ID of the requesting module
 * @return int64_t messageID
 */
int64_t SystemMessaging::subscribeToMessage(std::string messageName,
    uint64_t messageSize, int64_t moduleID)
{
    int64_t messageID;
    std::vector<AllowAccessData>::iterator it;
    messageID = this->FindMessageID(messageName);
    if(messageID < 0)
    {
        messageID = this->CreateNewMessage(messageName, messageSize, 2);
    }
    if(moduleID >= 0 && messageID >= 0)
    {
        it = this->messageStorage->subData.begin();
        it += messageID;
        it->accessList.insert(moduleID);
        it->publishedHere = false;
    }
    return(messageID);
}

/*!
 * This message gives the requesting module write rights if the module and message are valid
 * @param uint64_t messageID the ID of the message to write to
 * @param int64_t moduleID The ID of the requesting module
 * @return bool rightsObtained True if access was granted, else false
 */
bool SystemMessaging::obtainWriteRights(uint64_t messageID, int64_t moduleID)
{
    bool rightsObtained = false;
    
    if(moduleID >= 0 && messageID < this->GetMessageCount())
    {
        std::vector<AllowAccessData>::iterator it;
        it = this->messageStorage->pubData.begin();
        it += messageID;
        it->accessList.insert(moduleID);
        rightsObtained = true;
    }
    
    return(rightsObtained);
}

/*!
 * this method gives the requesting module permission to read the requested message
 * @param uint64_t messageID The message to get read rights to
 * @param int64_t moduleID The requesting module
 * @return bool rightsObtained True if rights granted, else false
 */
bool SystemMessaging::obtainReadRights(uint64_t messageID, int64_t moduleID)
{
 
    bool rightsObtained = false;
    
    if(moduleID >= 0 && messageID < this->GetMessageCount()) {
        std::vector<AllowAccessData>::iterator it;
        it = this->messageStorage->subData.begin();
        it += messageID;
        it->accessList.insert(moduleID);
        rightsObtained = true;
    }
    return(rightsObtained);
}

/*!
 *  This method checks ALL message buffers for a message with the given name
 * @param std::string messageName
 * @return MessageIdentData dataFound A chunk of info about the message including whether it was found or not
 */
MessageIdentData SystemMessaging::messagePublishSearch(std::string messageName)
{
    int64_t messageID;
    
    MessageIdentData dataFound;
    dataFound.itemFound = false;
    dataFound.itemID = -1;
    dataFound.processBuffer = ~0;
    std::vector<MessageStorageContainer *>::iterator it;
    for(it=this->dataBuffers.begin(); it != this->dataBuffers.end(); it++)
    {
        messageID = this->FindMessageID(messageName, it - this->dataBuffers.begin());
        if(messageID < 0)
        {
            continue;
        }
        dataFound.itemFound = true;
        dataFound.itemID = messageID;
        dataFound.processBuffer = it - this->dataBuffers.begin();
        dataFound.bufferName = (*it)->bufferName;
        std::vector<AllowAccessData>::iterator pubIt;
        pubIt=(*it)->pubData.begin() + messageID;
        if(pubIt->accessList.size() > 0 && pubIt->publishedHere)
        {
            return(dataFound);
        }
    }
    return(dataFound);
}

/*!
 * This method writes data to an already-created message if the requester has the right to
 * @param uin64_t MessageID The message to write to
 * @param uint64_t ClockTimeNanos The time to say the message was written in ns since sim start
 * @param uint64_t MsgSize Size of the message
 * @param void* MsgPayload The data in the message
 * @param int64_t moduleID The requester ID
 * @return bool -- whether or not the message was written
 */
bool SystemMessaging::WriteMessage(uint64_t MessageID, uint64_t ClockTimeNanos,
                                   uint64_t MsgSize, void *MsgPayload, int64_t moduleID)
{
    // Check if the message is valid
    if(MessageID >= this->GetMessageCount())
    {
        BSK_PRINT_BRIEF(MSG_ERROR, "Received a write request for invalid message ID: %llu \n"
                                   " from ModuleID: %lld \n ", MessageID, moduleID);
        this->WriteFails++;
        return(false);
    }
    // Check and update the previous publisher. Deny write if requester doesn't have pub access
    MessageHeaderData* MsgHdr = this->FindMsgHeader(MessageID);
    if(MsgHdr->previousPublisher != moduleID)
    {
        std::vector<AllowAccessData>::iterator it;
        it = this->messageStorage->pubData.begin();
        it += MessageID;
        if(it->accessList.find(moduleID) != it->accessList.end())
        {
            MsgHdr->previousPublisher = moduleID;
        }
        else
        {
            BSK_PRINT_BRIEF(MSG_ERROR, "Received a write request from a module that doesn't publish for %s . You get nothing.\n",
                            this->FindMessageName(MessageID).c_str());
            this->WriteFails++;
            return(false);
        }
    }
    // Check the message size
    if(MsgSize != MsgHdr->MaxMessageSize)
    {
        BSK_PRINT_BRIEF(MSG_ERROR, "Received a write request that was incorrect size for: %s . You get nothing.\n",
                  MsgHdr->MessageName);
        this->WriteFails++;
        return(false);
    }
    // If you made it this far, write the message and return success
    uint8_t *WriteDataBuffer = &(this->messageStorage->messageStorage.StorageBuffer[MsgHdr->
                                                               StartingOffset]);
    uint64_t AccessIndex = (MsgHdr->UpdateCounter%MsgHdr->MaxNumberBuffers)*
    (sizeof(SingleMessageHeader) + MsgHdr->MaxMessageSize);
    WriteDataBuffer += AccessIndex;
    SingleMessageHeader WriteHeader;
    WriteHeader.WriteClockNanos = ClockTimeNanos;
    WriteHeader.WriteSize = MsgSize;
    memcpy(WriteDataBuffer, &WriteHeader, sizeof(SingleMessageHeader));
    WriteDataBuffer += sizeof(SingleMessageHeader);
    memcpy(WriteDataBuffer, MsgPayload, MsgSize);
    MsgHdr->CurrentReadSize = MsgSize;
    MsgHdr->CurrentReadTime = ClockTimeNanos;
    MsgHdr->CurrentReadBuffer = MsgHdr->UpdateCounter%MsgHdr->MaxNumberBuffers;
    MsgHdr->UpdateCounter++;
    return(true);
}

/*! This method is static and is added so that other classes (ex. messageLogger)
 that have the messaging buffer layout can easily access their own internal
 buffers without having to re-write the same code.  Kind of overkill, but
 there you go.
 @param MsgBuffer The base address of the message buffer we are reading
 @param MsgBytes The maximum number of bytes for a given message type
 @param CurrentOffset The message count that we want to ready out
 @param DataHeader The message header that we are writing out to
 @param OutputBuffer The output message buffer we are writing out to
 @return void
 */
void SystemMessaging::AccessMessageData(uint8_t *MsgBuffer, uint64_t maxMsgBytes,
                                        uint64_t CurrentOffset, SingleMessageHeader *DataHeader,
                                        uint64_t maxReadBytes, uint8_t *OutputBuffer)
{
    MsgBuffer += CurrentOffset * (sizeof(SingleMessageHeader) +
                                  maxMsgBytes);
    memcpy(DataHeader, MsgBuffer, sizeof(SingleMessageHeader));
    uint64_t ReadSize = maxReadBytes < DataHeader->WriteSize ? maxReadBytes :
    DataHeader->WriteSize;
    MsgBuffer += sizeof(SingleMessageHeader);
    memcpy(OutputBuffer, MsgBuffer, ReadSize);
}

/*!
 * This method reads a message. A warning is thrown if the requester isn't supposed to be reading this message.
 * @param uint64_t MessageID  ID of the message to read
 * @param SingleMessageHeader* DataHeader Message header pointer to put message header data into
 * @param uint64_t MaxBytes The maximum number of bytes to read into MsgPayload
 * @param void* MsgPayload A pointer to memory to toss the message data into
 * @param int64_t moduleID The module requesting a read
 * @param uint64_t CurrentOffset
 * @return bool -- Whether the message was read successfully or not
 */
bool SystemMessaging::ReadMessage(uint64_t MessageID, SingleMessageHeader
                                  *DataHeader, uint64_t MaxBytes, void *MsgPayload, int64_t moduleID, uint64_t CurrentOffset)
{
    if(MessageID >= this->GetMessageCount())
    {
        BSK_PRINT_BRIEF(MSG_ERROR, "Received a read request for invalid message ID: %lld \n", MessageID);
        this->ReadFails++;
        return(false);
    }
    MessageHeaderData* MsgHdr = this->FindMsgHeader(MessageID);
    /// - If there is no data just alert caller that nothing came back
    if(MsgHdr->UpdateCounter == 0)
    {
        return(false);
    }
    int64_t CurrentIndex = MsgHdr->UpdateCounter % MsgHdr->MaxNumberBuffers;
    CurrentIndex -= (1 + CurrentOffset);
    while(CurrentIndex < 0)
    {
        CurrentIndex += MsgHdr->MaxNumberBuffers;
    }
    std::vector<MessageExchangeData>::iterator exIt;
    std::vector<AllowAccessData>::iterator accIt;
    accIt = this->messageStorage->subData.begin();
    exIt = this->messageStorage->exchangeData.begin();
    accIt += MessageID;
    exIt += MessageID;
    if(accIt->accessList.find(moduleID) == accIt->accessList.end()
        && moduleID != -1)
    {
        BSK_PRINT_BRIEF(MSG_WARNING, "Message %s was read by module ID %lld who is not on access list.\n", MsgHdr->MessageName, moduleID);
    }
    
    exIt->exchangeList.insert(std::pair<long int, long int>
        (MsgHdr->previousPublisher, moduleID));
    
    uint8_t *ReadBuffer = &(this->messageStorage->messageStorage.
                            StorageBuffer[MsgHdr->StartingOffset]);
    uint64_t MaxOutputBytes = MaxBytes < MsgHdr->MaxMessageSize ? MaxBytes :
    MsgHdr->MaxMessageSize;
    this->AccessMessageData(ReadBuffer, MsgHdr->MaxMessageSize, CurrentIndex,
                      DataHeader, MaxOutputBytes, reinterpret_cast<uint8_t*>(MsgPayload));
    return(true);
}

/*!
 * This method prints all message data from the current buffer
 * @return void
 */
void SystemMessaging::PrintAllMessageData()
{
    uint64_t TotalMessageCount = this->GetMessageCount();
    BSK_PRINT_BRIEF(MSG_INFORMATION, "Number of Messages: %lld \n", TotalMessageCount);
    for(uint64_t i=0; i<TotalMessageCount; i++)
    {
        this->PrintMessageStats(i);
    }
}

/*!
 * This method returns the MessageHeaderData for a MessageID in the bufferSelect buffer
 * @param uint64_t MessageID The message to query for the header
 * @param int32_t bufferSelect The buffer to query for the message
 * @return MessageHeaderdata* MsgHdr The data requested
 */
MessageHeaderData* SystemMessaging::FindMsgHeader(uint64_t MessageID, int32_t bufferSelect)
{
    MessageHeaderData* MsgHdr;
    if(MessageID >= this->GetMessageCount(bufferSelect))
    {
        return NULL;
    }
    MessageStorageContainer *localStorage = this->messageStorage;
    if(bufferSelect >= 0)
    {
        std::vector<MessageStorageContainer *>::iterator it;
        it = this->dataBuffers.begin();
        it += bufferSelect;
        localStorage = *it;
    }
    MsgHdr = reinterpret_cast<MessageHeaderData*> (&(localStorage->messageStorage.
                                                     StorageBuffer[sizeof(uint64_t)]));
    MsgHdr += MessageID;
    return(MsgHdr);
}

/*!
 *  This message prints MessageHeaderData information for the requested MessageID
 * @param uint64_t MessageID The message to query
 * @return void
 */
void SystemMessaging::PrintMessageStats(uint64_t MessageID)
{
    MessageHeaderData* MsgHdr = this->FindMsgHeader(MessageID);
    if(MsgHdr == NULL)
    {
        BSK_PRINT_BRIEF(MSG_ERROR, "Received a print request for ID: %llu That ID is not valid.\n", MessageID);
        return;
    }
    BSK_PRINT_BRIEF(MSG_INFORMATION, "INFORMATION:\n Name: %s\n Writes: %llu \n MsgSize: %llu \n NumberBuffers: %u\n MsgID: %llu\n",
              MsgHdr->MessageName, MsgHdr->UpdateCounter, MsgHdr->MaxMessageSize, MsgHdr->MaxNumberBuffers, MessageID);
}

/*!
 * Finds the message name for the requested message in the selected buffer
 * @param uint64_t MessageID The message to query for the name
 * @param int32_t bufferSelect The buffer to query for the message
 * @return std::string MessageName The name of the six fingered man
 */
std::string SystemMessaging::FindMessageName(uint64_t MessageID, int32_t bufferSelect)
{
    if(MessageID >= this->GetMessageCount(bufferSelect))
    {
        BSK_PRINT_BRIEF(MSG_WARNING, "WARING: Asked to find a message for invalid ID: %llu", MessageID);
    }
    MessageHeaderData* MsgHdr = this->FindMsgHeader(MessageID, bufferSelect);
    return(MsgHdr->MessageName);
    
}

/*!
 * This message takes a MessageName and gives a message ID
 * @param std::string MessageName The name to query for the ID
 * @param int32_t bufferSelect The buffer to query for the name
 * @return uint64_t -- the message ID
 */
int64_t SystemMessaging::FindMessageID(std::string MessageName, int32_t bufferSelect)
{
    MessageHeaderData* MsgHdr;
    for(uint64_t i=0; i<this->GetMessageCount(bufferSelect); i++)
    {
        MsgHdr = this->FindMsgHeader(i, bufferSelect);
        if(MessageName == std::string(MsgHdr->MessageName))
        {
            return(i);
        }
    }
    return(-1);
}

/*!
 * This method assigns a module ID to a new module and increments the NextModuleID counter
 * @return uint64_t nextModuleID the newly minted module ID
 */
uint64_t SystemMessaging::checkoutModuleID()
{
    return(this->nextModuleID++);
}

/*!
 * This method finds a buffer given a name
 * @param std::string bufferName
 * @return MessageStorageContainer* -- a pointer to the buffer. Or, return -1 if not found.
 */
int64_t SystemMessaging::findMessageBuffer(std::string bufferName)
{
    std::vector<MessageStorageContainer *>::iterator it;
    for(it = this->dataBuffers.begin(); it!= this->dataBuffers.end(); it++)
    {
        MessageStorageContainer *localContainer = (*it);
        if(localContainer->bufferName == bufferName)
        {
            return(it - this->dataBuffers.begin());
        }
    }
    return(-1);
}

/*!
 * This method returns a list of messages that no one has access to.
 * @return std::set<std::string> unpublishedList The list of message names that are unpublished.
 */
std::set<std::string> SystemMessaging::getUnpublishedMessages()
{
    std::set<std::string> unpublishedList;
    std::vector<AllowAccessData>::iterator it;
    for(it=this->messageStorage->pubData.begin(); it!=this->messageStorage->pubData.end();
        it++)
    {
        if(it->accessList.size() <= 0)
        {
            std::string unknownPub = SystemMessaging::GetInstance()->
                    FindMessageName(it - this->messageStorage->pubData.begin());
            unpublishedList.insert(unknownPub);
        }
    }
    return(unpublishedList);
}

/*!
 * This method searches across all message buffers to get unique message names in the sim
 * @return std::set<std::string> outputNames A list of unique message names in the whole sim
 */
std::set<std::string> SystemMessaging::getUniqueMessageNames()
{
    std::set<std::string> outputNames;
    std::vector<MessageStorageContainer *>::iterator it;
    for(it = this->dataBuffers.begin(); it != this->dataBuffers.end(); it++)
    {
        for(uint64_t i=0; i<this->GetMessageCount(it - this->dataBuffers.begin()); i++)
        {
            outputNames.insert(this->FindMessageName(i, it - this->dataBuffers.begin()));
            
        }
    }
    return(outputNames);
}

/*!
 * This message gets the exchangeData for a given messageID
 * @param uint64_t messageID
 * @return std::set<std::pair<long int, long int>> exchangeList
 */
std::set<std::pair<long int, long int>>
    SystemMessaging::getMessageExchangeData(uint64_t messageID)
{
    std::vector<MessageExchangeData>::iterator it;
    it = this->messageStorage->exchangeData.begin();
    it += messageID;
    return(it->exchangeList);
}
