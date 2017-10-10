using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;

namespace ImageBreaker
{
    class Program
    {
        static void Main(string[] args)
        {
            var files = Directory.EnumerateFiles(".\\images", "*.jpg");
            foreach (var path in files)
            {
                var file1 = Path.GetFileName(path);
                var file2 = file1 + ".txt";
           
                var list = new List<String>();

                Bitmap image = (Bitmap)Image.FromFile("images\\" + file1, true);
                Bitmap imageBoxed = new Bitmap(image);
                Pen pen = new Pen(Color.FromArgb(255, 0, 0), 2);

                var name = file1.Split('.');

                using (StreamReader sr = new StreamReader("images\\" + file2))
                {
                    var file = sr.ReadToEnd();
                    var separator = new string[] { "\n" };
                    var boxes = file.Split(separator, StringSplitOptions.None);
                    for (var i = 0; i < boxes.Length; i++)
                    {
                        var loc = boxes[i].Split('\t');
                        if (loc.Length >= 4)
                        {
                            var x1 = Int32.Parse(loc[0]);
                            var y1 = Int32.Parse(loc[1]);
                            var x2 = Int32.Parse(loc[2]);
                            var y2 = Int32.Parse(loc[3]);

                            using (Graphics g = Graphics.FromImage(imageBoxed))
                            {
                                g.DrawRectangle(pen, new Rectangle(x1, y1, x2 - x1 + 1, y2 - y1 + 1));
                            }

                            Bitmap bmp = new Bitmap(x2 - x1 + 1, y2 - y1 + 1);

                            for (var x = x1; x <= x2; x++)
                            {
                                for (var y = y1; y <= y2; y++)
                                {
                                    bmp.SetPixel(x - x1, y - y1, image.GetPixel(x, y));
                                }
                            }

                            var fileNamePng = "output\\" + name[0] + "_" + i.ToString() + ".png";
                            var fileNameTxt = "output\\" + name[0] + "_" + i.ToString();
                            bmp.Save(fileNamePng, System.Drawing.Imaging.ImageFormat.Png);
                            var p = Process.Start("C:\\Users\\ebrag\\AppData\\Local\\Tesseract-OCR\\tesseract.exe", fileNamePng + " " + fileNameTxt + " --psm 7 --oem 2");
                            p.WaitForExit();

                            using (StreamReader res = new StreamReader(fileNameTxt + ".txt"))
                            {
                                var result = res.ReadLine();
                                list.Add(boxes[i] + "\t\t\t" + result);
                            }
                        }
                    }

                    imageBoxed.Save("output\\" + name[0] + "_" + "result.png", System.Drawing.Imaging.ImageFormat.Png);
                     
                    using (StreamWriter sw = new StreamWriter("output\\" + name[0] + "_" + "result.txt"))
                    {
                        foreach (var line in list)
                        {
                            sw.WriteLine(line);
                        }
                    }
                }
            }
        }
    }
}
