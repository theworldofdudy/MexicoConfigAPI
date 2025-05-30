from enum import Enum
import struct
import sys

from fastapi import FastAPI
from pydantic import BaseModel

## backend -> frontend
from fastapi.middleware.cors import CORSMiddleware

class RegisterInput(BaseModel):
    registerString: str

class ModelName(str, Enum):
    alexnet = "alexnet"
    resnet = "resnet"
    lenet = "lenet"
    
class ConfigFileParser(object):
    def __init__(self, filename):
        self.filename : str = filename
        
        # La cabecera inicial de 6 bytes
        self.HEADER_SIZE = 6

        # Estructura tsICfgGenParam (18 bytes según los tipos de datos)
        self.TS_ICFG_GEN_PARAM_FORMAT = "4B8H"
        self.TS_ICFG_GEN_PARAM_SIZE = struct.calcsize(self.TS_ICFG_GEN_PARAM_FORMAT)
        
        self.tsICfgTicket_format = (
        "< H B 32s 32s 32s 32s B B 64s "  
        "B B B I B H B B B B B B B B "  
        "B B B B B B B B B B B B B B B B B B B B B B B B B B B B "  
        "2I 8s 8s H H "  
        "I I I I I "  
        "10I "  
        "10I "  
        "I I"  
    )

        # Estructura tsICfgOriginDestination (3 bytes: 1 byte Origen, 1 byte Destino, 1 byte Descuento)
        self.TS_ICFG_ORIGIN_DEST_FORMAT = "3B"
        self.TS_ICFG_TRANSFERS = "8B"
        self.TS_ICFG_TRANSFERS_SIZE = struct.calcsize(self.TS_ICFG_TRANSFERS)
        self.TS_ICFG_ORIGIN_DEST_SIZE = struct.calcsize(self.TS_ICFG_ORIGIN_DEST_FORMAT)

    def read_binary_file(self):
        with open(self.filename, "rb") as f:
            data = f.read()
        
        return data

    def parse_param_file(self, buffer):
        output = []
        offset = 0
        
        version = struct.unpack_from("<H", buffer, offset)[0]
        output.append(f"Version: {version}\n")

        # Saltar la cabecera de 6 bytes
        offset += self.HEADER_SIZE

        # Extraer tsICfgGenParam
        gen_param = struct.unpack_from(self.TS_ICFG_GEN_PARAM_FORMAT, buffer, offset)
        offset += self.TS_ICFG_GEN_PARAM_SIZE

        output.append("===== tsICfgGenParam =====\n")
        output.append(f"bCSCUpperVersion: {gen_param[0]}\n")
        output.append(f"bCSCLowerVersion: {gen_param[1]}\n")
        output.append(f"bCPSCUpperVersion: {gen_param[2]}\n")
        output.append(f"bCPSCLowerVersion: {gen_param[3]}\n")
        output.append(f"wPassbackTime: {gen_param[4]}\n")
        output.append(f"wMinDiscount: {gen_param[5]}\n")
        output.append(f"wMiddleMinDiscount: {gen_param[6]}\n")
        output.append(f"wMiddleMaxDiscount: {gen_param[7]}\n")
        output.append(f"wMaxDiscount: {gen_param[8]}\n")
        output.append(f"wQRMaxValidityTime: {gen_param[9]}\n")
        output.append(f"wQRMaxValidationTime: {gen_param[10]}\n")
        output.append(f"wNumofActiveStations: {gen_param[11]}\n")
        output.append("=========================\n")
        
        # Leer los registros de tsICfgOriginDestination hasta el final del buffer
        output.append("\n===== tsICfgOriginDestination Records =====\n")
        
        zones = []
        while offset + self.TS_ICFG_ORIGIN_DEST_SIZE <= len(buffer):
            origin_dest = struct.unpack_from(self.TS_ICFG_ORIGIN_DEST_FORMAT, buffer, offset)
            offset += self.TS_ICFG_ORIGIN_DEST_SIZE
            output.append(f"Origen: {origin_dest[0]}, Destino: {origin_dest[1]}, Descuento: {origin_dest[2]}\n")
            zones.append(origin_dest)

        output.append("===========================================\n")
        
        return gen_param, zones
    
    
    def parse_titulos_file(self, data):
        output = []
        
        tsICfgTicket_size = struct.calcsize(self.tsICfgTicket_format)

        version_bytes = data[:2]
        version = struct.unpack("<H", version_bytes)[0]
        output.append(f"Tamaño esperado de tsICfgTicket: {tsICfgTicket_size} bytes")
        output.append(f"Version: {version}\n")

        offset = self.HEADER_SIZE

        while offset < len(data):
            chunk = data[offset:offset + tsICfgTicket_size]

            if len(chunk) < tsICfgTicket_size:
                output.append(f"Error: chunk leído ({len(chunk)} bytes) es menor que el tamaño esperado ({tsICfgTicket_size} bytes).")
                break

            ticket = struct.unpack(self.tsICfgTicket_format, chunk)
            baSpanishName = ticket[2].decode('latin1').strip('\x00')
            baEnglishName = ticket[3].decode('latin1').strip('\x00')
            baFrenchName = ticket[4].decode('latin1').strip('\x00')
            baGermanName = ticket[5].decode('latin1').strip('\x00')
            
            """baaTransferTimes = [list(ticket[8][i * 8:(i + 1) * 8]) for i in range(8)]
            baNoEntryTransferTimes = list(ticket[56:64])
            baTransferPenaltyTimes = list(ticket[64:72])
            raw_discounts = ticket[72:82]  # 10 DWORDs
            raw_midle_discounts = ticket[82:92]  # 10 DWORDs """

            baaTransferTimes = []
            offset2 = offset + 8
            for i in range(8):
                unpacked_data  = struct.unpack_from(self.TS_ICFG_TRANSFERS, data, offset2)
                offset2 += self.TS_ICFG_TRANSFERS_SIZE
                baaTransferTimes.append( unpacked_data )

            baNoEntryTransferTimes = list(ticket[53])
            baTransferPenaltyTimes = list(ticket[54])
            raw_discounts = ticket[62:72]  # 10 DWORDs
            raw_midle_discounts = ticket[72:82]  # 10 DWORDs

            tsaDiscount = [(raw_discounts[i], raw_discounts[i + 1]) for i in range(0, len(raw_discounts), 2)]
            tsaMidleDiscount = [(raw_midle_discounts[i], raw_midle_discounts[i + 1]) for i in range(0, len(raw_midle_discounts), 2)]
            
            output.append(f"Ticket Code: {ticket[0]}\n")
            output.append(f"Fare Type: {ticket[1]}\n")
            output.append(f"Spanish Name: {baSpanishName}\n")
            output.append(f"English Name: {baEnglishName}\n")
            output.append(f"French Name: {baFrenchName}\n")
            output.append(f"German Name: {baGermanName}\n")
            output.append(f"Representation Type: {ticket[6]}\n")
            output.append(f"Area Control: {ticket[7]}\n")
            output.append(f"Day Validity: {ticket[9]}\n")
            output.append(f"Week Validity: {ticket[10]}\n")
            output.append(f"Proprietary Company: {ticket[11]}\n")
            output.append(f"Valid Operators: {ticket[12]}\n")
            output.append(f"Balance Type: {ticket[13]}\n")
            output.append(f"Number of Trips: {ticket[14]}\n")
            output.append(f"Balance Period Value: {ticket[15]}\n")
            output.append(f"Balance Period Units: {ticket[16]}\n")
            output.append(f"Time Validity Exp Type At Sale: {ticket[17]}\n")
            output.append(f"Time Validity Begin Type At Val: {ticket[18]}\n")
            output.append(f"Time Validity Exp Type At Val: {ticket[19]}\n")
            output.append(f"Time Validity Begin At Val Ctrl: {ticket[20]}\n")
            output.append(f"Time Validity Exp At Val Ctrl: {ticket[21]}\n")
            output.append(f"No Entry Transfer Times: {baNoEntryTransferTimes}\n")
            output.append(f"Transfer Penalty Times: {baTransferPenaltyTimes}\n")
            output.append(f"Discounts: {tsaDiscount}\n")
            output.append(f"Middle Discounts: {tsaMidleDiscount}\n")
            output.append(f"Max Entry to Exit Time: {ticket[32]}\n")
            output.append("-" * 50)

            offset += tsICfgTicket_size

        return output, baaTransferTimes

    def parse_titulos_file2(self, data):
        titulos = []
        
        tsICfgTicket_size = struct.calcsize(self.tsICfgTicket_format)

        version_bytes = data[:2]
        version = struct.unpack("<H", version_bytes)[0]

        offset = self.HEADER_SIZE

        while offset < len(data):
            output = []
            output.append(f"Tamaño esperado de tsICfgTicket: {tsICfgTicket_size} bytes")
            output.append(f"Version: {version}\n")
            chunk = data[offset:offset + tsICfgTicket_size]

            if len(chunk) < tsICfgTicket_size:
                output.append(f"Error: chunk leído ({len(chunk)} bytes) es menor que el tamaño esperado ({tsICfgTicket_size} bytes).")
                break

            ticket = struct.unpack(self.tsICfgTicket_format, chunk)
            baSpanishName = ticket[2].decode('latin1').strip('\x00')
            baEnglishName = ticket[3].decode('latin1').strip('\x00')
            baFrenchName = ticket[4].decode('latin1').strip('\x00')
            baGermanName = ticket[5].decode('latin1').strip('\x00')
            
            """baaTransferTimes = [list(ticket[8][i * 8:(i + 1) * 8]) for i in range(8)]
            baNoEntryTransferTimes = list(ticket[56:64])
            baTransferPenaltyTimes = list(ticket[64:72])
            raw_discounts = ticket[72:82]  # 10 DWORDs
            raw_midle_discounts = ticket[82:92]  # 10 DWORDs """

            baaTransferTimes = []
            offset2 = offset + 8
            for i in range(8):
                unpacked_data  = struct.unpack_from(self.TS_ICFG_TRANSFERS, data, offset2)
                offset2 += self.TS_ICFG_TRANSFERS_SIZE
                baaTransferTimes.append( unpacked_data )

            baNoEntryTransferTimes = list(ticket[53])
            baTransferPenaltyTimes = list(ticket[54])
            raw_discounts = ticket[62:72]  # 10 DWORDs
            raw_midle_discounts = ticket[72:82]  # 10 DWORDs

            tsaDiscount = [(raw_discounts[i], raw_discounts[i + 1]) for i in range(0, len(raw_discounts), 2)]
            tsaMidleDiscount = [(raw_midle_discounts[i], raw_midle_discounts[i + 1]) for i in range(0, len(raw_midle_discounts), 2)]
            
            output.append(f"Ticket Code: {ticket[0]}\n")
            output.append(f"Fare Type: {ticket[1]}\n")
            output.append(f"Spanish Name: {baSpanishName}\n")
            output.append(f"English Name: {baEnglishName}\n")
            output.append(f"French Name: {baFrenchName}\n")
            output.append(f"German Name: {baGermanName}\n")
            output.append(f"Representation Type: {ticket[6]}\n")
            output.append(f"Area Control: {ticket[7]}\n")
            output.append(f"Day Validity: {ticket[9]}\n")
            output.append(f"Week Validity: {ticket[10]}\n")
            output.append(f"Proprietary Company: {ticket[11]}\n")
            output.append(f"Valid Operators: {ticket[12]}\n")
            output.append(f"Balance Type: {ticket[13]}\n")
            output.append(f"Number of Trips: {ticket[14]}\n")
            output.append(f"Balance Period Value: {ticket[15]}\n")
            output.append(f"Balance Period Units: {ticket[16]}\n")
            output.append(f"Time Validity Exp Type At Sale: {ticket[17]}\n")
            output.append(f"Time Validity Begin Type At Val: {ticket[18]}\n")
            output.append(f"Time Validity Exp Type At Val: {ticket[19]}\n")
            output.append(f"Time Validity Begin At Val Ctrl: {ticket[20]}\n")
            output.append(f"Time Validity Exp At Val Ctrl: {ticket[21]}\n")
            output.append(f"No Entry Transfer Times: {baNoEntryTransferTimes}\n")
            output.append(f"Transfer Penalty Times: {baTransferPenaltyTimes}\n")
            output.append(f"Discounts: {tsaDiscount}\n")
            output.append(f"Middle Discounts: {tsaMidleDiscount}\n")
            output.append(f"Max Entry to Exit Time: {ticket[32]}\n")
            output.append("-" * 50)

            offset += tsICfgTicket_size
            
            titulos.append(output)

        return titulos, baaTransferTimes
    
    
class RegisterParser(object):
    def __init__(self, register_string):
        self.register_string = register_string
        
    # Función para obtener un subconjunto de bits
    def obtener_bits(self, data, start_bit, size_bits):
        return data[start_bit:start_bit + size_bits]

    # Función para convertir una cadena binaria a decimal
    def bin_a_decimal(bin_str):
        return int(bin_str, 2)

    def bits_to_decimal_lsb(self, bits):
        # 1. Rellenamos a múltiplo de 8
        bits_padded = bits.zfill((len(bits) + 7) // 8 * 8)

        # 2. Agrupamos en bytes (8 bits), convertimos a int y formateamos a hex
        byte_list = [int(bits_padded[i:i+8], 2) for i in range(0, len(bits_padded), 8)]

        # 3. Invertimos los bytes (LSB → MSB)
        reversed_bytes = byte_list[::-1]

        # Convierte a decimal como si fuera un número base-256
        result = 0
        for b in reversed_bytes:
            result = (result << 8) | b

        return result

    def parse(self):
        # Convertimos la cadena hexadecimal a binario
        data = bin(int(self.register_string, 16))[2:].zfill(len(self.register_string) * 4)  # Aseguramos que tenga los bits correctos

        print(f"Cadena binaria: {data}")
        # Revertir la secuencia de bits para tratarla como LSB (Least Significant Bit first)
        """     data = ''.join(reversed([data[i:i + 8] for i in range(0, len(data), 8)]))
        data = ''.join(data)
        print(f"Cadena binaria LSB: {data}") """

        # Definición de las variables con las posiciones en bits y tamaños en bits
        result = {}
        
        #Cabecera 11 bytes. Le quitamos la cabecera a data
        data = data[88:]  # 11 bytes = 88 bits
        

        # Asignamos los datos a las variables indicadas (usando posiciones y tamaños en bits)
        #result['l_bpAux'] = data
        #result['l_bUidAux'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 0, 56))  # 56 bits
        result['bType'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 56, 4))  # 4 bits
        result['bSubType'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 60, 4))  # 4 bits
        result['bVersion'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 64, 4))  # 4 bits
        result['bCompany'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 68, 5))  # 5 bits
        result['bEndOfValidityDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 73, 5))  # 5 bits
        result['bEndOfValidityMonth'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 78, 4))  # 4 bits
        result['bEndOfValidityYear'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 82, 5))  # 5 bits
        result['bCardEnabled'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 87, 1))  # 1 bit
        result['bTransactionNumber'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 88, 4))  # 4 bits
        result['bEnabledTickets'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 104, 4))  # 4 bits
        result['bLastTicketUsed'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 108, 2))  # 2 bits
        result['bCompany_2'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 120, 5))  # 5 bits
        result['wCode'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 125, 12))  # 12 bits
        result['bDayValidity'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 137, 4))  # 4 bits
        result['bWeekValidity'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 141, 4))  # 4 bits
        result['bFareType'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 145, 4))  # 4 bits
        result['bFareIndex'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 149, 3))  # 3 bits
        result['bZoneValidity'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 152, 8))  # 8 bits
        result['bTypeOfTimeValidityUnits'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 160, 3))  # 3 bits
        result['bNoOfTimeValidityUnits'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 163, 8))  # 8 bits
        result['bUseTripsBalance'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 171, 1))  # 1 bit
        result['bPrevTicketIsExtended'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 184, 1))  # 1 bit
        result['bPrevTimeValidityDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 185, 5))  # 5 bits
        result['bPrevTimeValidityMonth'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 190, 4))  # 4 bits
        result['bPrevTimeValidityYear'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 194, 5))  # 5 bits
        result['bPrevTimeValidityHour'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 199, 5))  # 5 bits
        result['bPrevTimeValidityMinute'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 204, 6))  # 6 bits
        result['bPrevTripBalance'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 210, 8))  # 8 bits
        result['bPrevDayTripCounter'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 218, 3))  # 3 bits
        result['bPrevLastValidationDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 221, 5))  # 5 bits
        result['bTicketIsExtended'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 240, 1))  # 1 bit
        result['bTimeValidityDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 241, 5))  # 5 bits
        result['bTimeValidityMonth'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 246, 4))  # 4 bits
        result['bTimeValidityYear'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 250, 5))  # 5 bits
        result['bTimeValidityHour'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 255, 5))  # 5 bits
        result['bTimeValidityMinute'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 260, 6))  # 6 bits
        result['bTripBalance'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 266, 8))  # 8 bits
        result['bDayTripCounter'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 274, 3))  # 3 bits
        result['bLastValidationDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 277, 5))  # 5 bits
        result['bPrevValidationOperator'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 296, 5))  # 5 bits
        result['bPrevValidationType'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 301, 5))  # 5 bits
        result['wPrevValidationPlace'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 306, 13))  # 13 bits
        result['bPrevValidationDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 319, 5))  # 5 bits
        result['bPrevValidationMonth'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 324, 4))  # 4 bits
        result['bPrevValidationYear'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 328, 5))  # 5 bits
        result['bPrevValidationHour'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 333, 5))  # 5 bits
        result['bPrevValidationMinute'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 338, 6))  # 6 bits
        result['bPrevNoOfPassengersTravelling'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 350, 6))  # 6 bits
        result['bPrevNoOfPassengersExiting'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 356, 6))  # 6 bits
        result['bPrevBlackListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 362, 1))  # 1 bit
        result['bPrevGreyListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 363, 1))  # 1 bit
        result['bPrevWhiteListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 364, 1))  # 1 bit
        result['bPrevEntryExitControl'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 365, 1))  # 1 bit
        result['bOperator'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 376, 5))  # 5 bits
        result['bType_2'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 381, 5))  # 5 bits
        result['wValidationPlace'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 386, 13))  # 13 bits
        result['bValidationDay'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 399, 5))  # 5 bits
        result['bValidationMonth'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 404, 4))  # 4 bits
        result['bValidationYear'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 408, 5))  # 5 bits
        result['bValidationHour'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 413, 5))  # 5 bits
        result['bValidationMinute'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 418, 6))  # 6 bits
        result['bValidationSecond'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 424, 6))  # 6 bits
        result['bNoOfPassengersTravelling'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 430, 6))  # 6 bits
        result['bNoOfPassengersExiting'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 436, 6))  # 6 bits
        result['bBlackListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 442, 1))  # 1 bit
        result['bGreyListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 443, 1))  # 1 bit
        result['bWhiteListBit'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 444, 1))  # 1 bit
        result['bEntryExitControl'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 445, 1))  # 1 bit

        result['l_spPurse->dwValue'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 456, 32))  # 32 bit
        result['dwPurseDiscount'] = self.bits_to_decimal_lsb(self.obtener_bits(data, 488, 32))  # 32 bit
        result['CRC'] = self.bits_to_decimal_lsb(self.obtener_bits(data, len(data) -16, 16))  # 16 bit

        return result

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cambia "*" por el dominio de tu frontend en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "¡Hola desde la API de Carlos!"}

@app.get("/data/{item_id}")
def read_item(item_id: int, q: str = "hola"):
    return {"item_id": item_id, "query": q}

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}

@app.get("/param")
async def read_param_file():
    configClass = ConfigFileParser("documents/paramval.dat")
    buffer = configClass.read_binary_file()
    gen_param, zones = configClass.parse_param_file(buffer)
    return {"bCSCUpperVersion:": gen_param[0] ,
            "bCSCLowerVersion:": gen_param[1],
            "bCPSCUpperVersion:": gen_param[2],
            "bCPSCLowerVersion:": gen_param[3],
            "wPassbackTime:": gen_param[4],
            "wMinDiscount:": gen_param[5],
            "wMiddleMinDiscount:": gen_param[6],
            "wMiddleMaxDiscount:": gen_param[7],
            "wMaxDiscount:": gen_param[8],
            "wQRMaxValidityTime:": gen_param[9],
            "wQRMaxValidationTime:": gen_param[10],
            "wNumofActiveStations:": gen_param[11],
            "zones": zones}

@app.get("/titulos")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file(buffer)
    print(baaTransferTimes)
    return {"Ticket size": data[0],
            "Config version": data[1],
            "Ticket Code": data[2],
            "Fare Type": data[3],
            "Spanish Name": data[4],
            "English Name": data[5],
            "French Name": data[6],
            "German Name": data[7],
            "Representation Type": data[8],
            "Area Control": data[9],
            "TransferTimes": baaTransferTimes,
            "Day Validity": data[10],
            "Week Validity": data[11],
            "Proprietary Company": data[12],
            "Valid Operators": data[13],
            "Balance Type": data[14],
            "Number of Trips": data[15],
            "Balance Period Value": data[16],
            "Balance Period Units": data[17],
            "Time Validity Exp Type At Sale": data[18],
            "Time Validity Begin Type At Val": data[19],
            "Time Validity Exp Type At Val": data[20],
            "Time Validity Begin At Val Ctrl": data[21],
            "Time Validity Exp At Val Ctrl": data[22],
            "No Entry Transfer Times": data[23],
            "Transfer Penalty Times": data[24],
            "Discounts": data[25],
            "Middle Discounts": data[26],
            "Max Entry to Exit Time": data[27]}
    
""" @app.get("/titulos2")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file2(buffer)
    print(baaTransferTimes)
    print("data Size:", len(data))
    for i in range(len(data)):
        print(data[i])
    
    return {"data": data} """


@app.get("/titulos2")
async def read_param_file():
    configClass = ConfigFileParser("documents/titulosval.dat")
    buffer = configClass.read_binary_file()
    data, baaTransferTimes = configClass.parse_titulos_file2(buffer)
    print(baaTransferTimes)
    print("data Size:", len(data))
    for i in range(len(data)):
        print(data[i])
    
    return {"data": data}


'''puedo probar con curl
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  --request POST \
  -d "{\"registerString\": \"hola desde curl\"}"
  '''
  
@app.post("/register")
async def register_decoder(register_input: RegisterInput):
    register_string = register_input.registerString
    # Aquí puedes procesar el register_string como necesites
    print(f"Register String: {register_string}")
    
    registerClass = RegisterParser(register_string)
    data = registerClass.parse()  
    print(data)
    print("data Size:", len(data))

    # Mostrar algunos resultados
    for key in data:
        #print(f"{key}: {result[key]}")
        value = int(data[key])
        print(key, "-> dec:", value, "-> hex:", hex(value), "-> bin:", bin(value))
    
    return data #devuelve el dict directamente
