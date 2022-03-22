import logging
import json
from pytesseract import image_to_data, Output
from read_api import ReadApi


class TesseractOcr():
    """
    Class to implement OCR recognition
    """

    def __init__(self, log, config, read_api_status):
        self.logging = log
        self.config = config
        self.read_api_status = read_api_status

    def tesseract_read(self, crop_img):
        """
        Tesseract OCR processing
        """
        try:
            self.logging.info("Calling recognition engine")
            text = image_to_data(crop_img, output_type=Output.DICT)
            confidence = text.get("conf")
            self.logging.info("Recognition of region sucessful")
        except Exception as ex:
            self.logging.exception("Error in calling tesseract")
            self.logging.exception(str(ex))
        mean_confidence = 0
        confidence_sum = 0
        count = 0
        selected_text = ""
        try:
            for index, item in enumerate(confidence):
                if (int(item) != -1):
                    text_value = text.get("text")
                    selected_text = selected_text + text_value[index] + " "
                    confidence_sum = confidence_sum + int(item)
                    count = count + 1
            if selected_text:
                selected_text = selected_text.strip()
        except Exception as ex:
            self.logging.exception("Error in confidence calculation")
            self.logging.exception(str(ex))
        if count != 0:
            mean_confidence = confidence_sum / count
        return (selected_text, mean_confidence)

    def crop_image(self, img):
        """
        Crop parts of image for zonal OCR
        """
        tess_result = None
        try:
            y_axis = int(self.region_shape_attributes.get("y"))
            height = int(self.region_shape_attributes.get("height"))
            x_axis = int(self.region_shape_attributes.get("x"))
            width = int(self.region_shape_attributes.get("width"))
            region_name = self.region_attributes.get("Name")
            self.logging.info("Region: ")
            self.logging.info(region_name)
            crop_img = img[y_axis: y_axis + height, x_axis: x_axis + width]

            if self.read_api_status:
                logging.info("Calling read_api")
                read_api_obj = ReadApi(self.config, self.logging)
                tess_recog = read_api_obj.call_read_api(crop_img, height, width)
            else:
                logging.info("Calling tesseract_ocr")
                tess_recog = self.tesseract_read(crop_img)
            if tess_recog:
                tess_result = (region_name, tess_recog[0], tess_recog[1])
            else:
                tess_result = (region_name, None, 0)
        except Exception as ex:
            self.logging.exception("Error in crop_image()")
            self.logging.exception(str(ex))
        return tess_result

    def get_image(self, img, regions_list):
        """
        Get image and region details from api
        for cropping.
        """
        recognition_list = []
        self.logging.info("Starting image recognition.")
        try:
            for regions in regions_list:
                self.region_shape_attributes = regions.get("shape_attributes")
                self.region_attributes = regions.get("region_attributes")
                tess_recog = self.crop_image(img)
                if tess_recog:
                    json_body = {}
                    json_body["regionAttributeKey"] = tess_recog[0]
                    json_body["regionAttributeValue"] = tess_recog[1]
                    json_body["confidence"] = tess_recog[2]
                    recognition_list.append(json_body)
            self.logging.info("Image recognition completed.")
        except Exception as ex:
            self.logging.exception("Error in get_image()")
            self.logging.exception(str(ex))
        return recognition_list
