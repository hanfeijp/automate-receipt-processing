using WebOCR.Models;
using System.Collections.Generic;
using System.Net;
using System.Web.Http;
using System.IO;
using Newtonsoft.Json.Linq;
using Tesseract;
using System.Drawing;
using System;

namespace WebOCR.Controllers
{
    public class ProductsController : ApiController
    {
        private byte[] ImageData(System.Drawing.Image image, System.Drawing.Imaging.ImageFormat format)
        {
            using (MemoryStream ms = new MemoryStream())
            {
                // Convert Image to byte[]
                image.Save(ms, format);
                return ms.ToArray();
            }
        }

        public IEnumerable<Product> Get(string url)
        {
            var list = new List<Product>();

            try
            {
                var request = WebRequest.Create(url);

                using (var response = request.GetResponse())
                {
                    using (var stream = response.GetResponseStream())
                    {
                        var img = Bitmap.FromStream(stream);
                        var image = new Bitmap(img);

                        var mappedPath = System.Web.Hosting.HostingEnvironment.MapPath(@"~/tessdata");

                        using (var engine = new TesseractEngine(mappedPath, "eng", EngineMode.TesseractAndCube))
                        {
                            using (var pix = PixConverter.ToPix(image))
                            {
                                using (var page = engine.Process(pix, PageSegMode.OsdOnly))
                                {
                                    var orientation = Orientation.PageUp;
                                    var confidence = 0.0f;

                                    page.DetectBestOrientation(out orientation, out confidence);
                                }

                                using (WebClient client = new WebClient())
                                {
                                    byte[] data = ImageData(image, System.Drawing.Imaging.ImageFormat.Png);
                                    byte[] res = client.UploadData("http://ctpn.northeurope.cloudapp.azure.com", data);

                                    string result = System.Text.Encoding.UTF8.GetString(res);

                                    var json = JObject.Parse(result);
                                    var lines = json.Value<int>("Lines");

                                    if (lines > 0)
                                    {
                                        var regions = json.GetValue("Regions") as JArray;

                                        foreach (var box in regions)
                                        {
                                            var prod = new Product()
                                            {
                                                Type = "CTPN",
                                                BoundingBox = (box as JObject).Value<string>("BoundingBox"),
                                                TextAccuracy = float.Parse((box as JObject).Value<string>("Accuracy"))
                                            };

                                            var coord = prod.BoundingBox.Split(',');

                                            prod.SetX(Int32.Parse(coord[0]));
                                            prod.SetY(Int32.Parse(coord[1]));
                                            prod.SetX2(Int32.Parse(coord[2]));
                                            prod.SetY2(Int32.Parse(coord[3]));

                                            using (var page = engine.Process(pix, new Rect(prod.X(), prod.Y(), prod.X2() - prod.X() + 1, prod.Y2() - prod.Y() + 1), PageSegMode.SingleLine))
                                            {
                                                prod.OCRText = page.GetText().Trim();
                                                prod.OCRAccuracy = page.GetMeanConfidence();
                                            }
                                            list.Add(prod);
                                        }

                                        list.Sort(delegate (Product x, Product y)
                                        {
                                            if (x.Y() < y.Y()) return -1;
                                            else if (x.Y() == y.Y())
                                            {
                                                if (x.X() < y.X()) return -1;
                                                else if (x.X() == y.X()) return 0;
                                                return 1;
                                            }
                                            else return 1;
                                        });

                                        var total = "";
                                        var minX = image.Width;
                                        var minY = image.Height;
                                        var maxX = 0;
                                        var maxY = 0;
                                        var ocr_accuracy = 0.0f;
                                        var txt_accuracy = 0.0f;

                                        foreach (var line in list)
                                        {
                                            total += line.OCRText + " ";
                                            if (line.X() < minX) minX = line.X();
                                            if (line.Y() < minY) minY = line.Y();

                                            if (line.X2() > maxX) maxX = line.X2();
                                            if (line.Y2() > maxY) maxY = line.Y2();

                                            ocr_accuracy += line.OCRAccuracy;
                                            txt_accuracy += line.TextAccuracy;
                                        }

                                        list.Add(new Product()
                                        {
                                            Type = "COMBINED",
                                            BoundingBox = minX.ToString() + "," + minY.ToString() + "," + maxX.ToString() + "," + maxY.ToString(),
                                            TextAccuracy = txt_accuracy / lines,
                                            OCRText = total,
                                            OCRAccuracy = ocr_accuracy / lines
                                        });
                                    }
                                }

                                using (var page = engine.Process(pix))
                                {
                                    var prod = new Product()
                                    {
                                        Type = "FULL",
                                        BoundingBox = "0,0," + image.Width.ToString() + "," + image.Height.ToString(),
                                        OCRText = page.GetText().Replace("  ", " ").Replace(" \n", "\n").Replace("\n\n", "\n"),
                                        OCRAccuracy = page.GetMeanConfidence()
                                    };

                                    list.Add(prod);
                                }
                            }
                        }
                    }
                }
            }
            catch (Exception) {}

            return list.ToArray();
        }
    }
}
