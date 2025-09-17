import requests
import os
import re
import shutil
import argparse
from urllib.parse import urlparse
from collections import defaultdict
from pathlib import Path

try:
    import imagehash
    from PIL import Image
    DEDUPLICATION_AVAILABLE = True
except ImportError:
    DEDUPLICATION_AVAILABLE = False
    print("Warning: imagehash and PIL not available. Install with: pip install imagehash Pillow")

def load_urls_from_dom(file_path):
    """从DOM.txt文件中提取大尺寸JPG图片URL"""
    urls = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # 使用正则表达式提取src属性中的JPG URL
            url_pattern = r'src="(https://[^"]+\.jpe?g)"'
            matches = re.findall(url_pattern, content, re.IGNORECASE)
            urls.extend(matches)

            # 也匹配srcset中的JPG URL
            srcset_pattern = r'srcset="([^"]*)"'
            srcset_matches = re.findall(srcset_pattern, content)
            for srcset in srcset_matches:
                # 从srcset中提取JPG URL
                srcset_urls = re.findall(r'(https://[^\s,]+\.jpe?g)', srcset, re.IGNORECASE)
                urls.extend(srcset_urls)
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return []
    except Exception as e:
        print(f"读取文件时出错: {e}")
        return []

    # 去重
    unique_urls = list(set(urls))

    # 只保留大尺寸图片 (1152, 1344, 1536)
    large_urls = []
    for url in unique_urls:
        if any(size in url for size in ['1152', '1344', '1536']):
            large_urls.append(url)

    return large_urls

def get_domain_folder(url):
    """从URL中提取域名作为文件夹名"""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    # 移除www前缀并清理域名
    if domain.startswith('www.'):
        domain = domain[4:]
    # 替换不合法的文件夹字符
    domain = re.sub(r'[<>:"/\\|?*]', '_', domain)
    return domain

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Download URLs from DOM.txt and manage duplicates')
    parser.add_argument('--remove-filename-duplicates', action='store_true',
                       help='Remove filename-based duplicates after download')
    parser.add_argument('--skip-perceptual-dedup', action='store_true',
                       help='Skip perceptual hash deduplication')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Skip cleaning existing photos')
    parser.add_argument('--only-remove-duplicates', action='store_true',
                       help='Only remove filename duplicates, skip download')
    return parser.parse_args()

# 清理现有照片功能
def cleanup_existing_photos(downloads_dir="downloads"):
    """清理现有的照片和备份文件夹"""
    print(f"{'='*50}")
    print("清理现有照片...")
    print(f"{'='*50}")

    # 统计现有文件
    existing_count = 0
    backup_folders = []

    # 查找现有照片
    if os.path.exists(downloads_dir):
        for root, dirs, files in os.walk(downloads_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                    existing_count += 1

    # 查找备份文件夹
    for item in os.listdir('.'):
        if os.path.isdir(item) and ('backup' in item.lower() or 'duplicat' in item.lower()):
            backup_folders.append(item)

    if existing_count == 0 and len(backup_folders) == 0:
        print("没有找到现有照片或备份文件夹")
        return

    print(f"找到 {existing_count} 个现有照片")
    print(f"找到 {len(backup_folders)} 个备份文件夹")

    # 直接删除现有下载文件夹
    if existing_count > 0 and os.path.exists(downloads_dir):
        try:
            shutil.rmtree(downloads_dir)
            print(f"  已删除下载文件夹")
        except Exception as e:
            print(f"  删除失败: {e}")

    # 删除所有备份文件夹
    if len(backup_folders) > 0:
        for folder in backup_folders:
            try:
                shutil.rmtree(folder)
                print(f"  已删除备份文件夹: {folder}")
            except Exception as e:
                print(f"  删除失败 {folder}: {e}")

    # 重新创建下载目录
    os.makedirs(downloads_dir, exist_ok=True)
    print("清理完成，准备重新下载")

def main():
    """Main function with command line argument handling."""
    args = parse_arguments()

    # If only removing duplicates, skip everything else
    if args.only_remove_duplicates:
        remove_filename_duplicates()
        return

    # 执行清理（可选）
    if not args.skip_cleanup:
        cleanup_existing_photos()

    # 从DOM.txt加载URLs
    urls = load_urls_from_dom("DOM.txt")
    print(f"从DOM.txt中找到 {len(urls)} 个大尺寸JPG图片URL")

    if not urls:
        print("没有找到任何URL，退出程序")
        return

    # Download URLs
    download_urls(urls)

    # Process downloads based on arguments
    process_downloads(args)

def get_unique_filename(folder, filename):
    """如果文件已存在，自动加 _1、_2 ... 后缀"""
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(folder, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def remove_filename_duplicates():
    """Remove duplicate images based on filename pattern (keeping highest resolution)."""
    print(f"\n{'='*50}")
    print("开始移除文件名重复...")
    print(f"{'='*50}")

    downloads_dir = Path("downloads")
    if not downloads_dir.exists():
        print("Downloads目录不存在")
        return

    # Find all image files
    image_files = []
    for img_file in downloads_dir.rglob("*.jpg"):
        image_files.append(img_file)

    # Group files by base name (without resolution suffix)
    file_groups = {}
    pattern = r'^(.+)-cc_ft_(\d+)\.jpg$'

    for img_file in image_files:
        match = re.match(pattern, img_file.name)
        if match:
            base_name = match.group(1)
            resolution = int(match.group(2))

            if base_name not in file_groups:
                file_groups[base_name] = []

            file_groups[base_name].append((img_file, resolution))

    # Remove duplicates, keeping highest resolution
    removed_count = 0
    total_size_saved = 0

    for base_name, files in file_groups.items():
        if len(files) > 1:
            # Sort by resolution (highest first)
            files.sort(key=lambda x: x[1], reverse=True)

            # Keep the first (highest resolution), remove the rest
            files_to_remove = files[1:]

            print(f"发现重复文件组: {base_name}")
            print(f"  保留: {files[0][0].name} ({files[0][1]}px)")

            for file_path, resolution in files_to_remove:
                try:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    print(f"  移除: {file_path.name} ({resolution}px)")
                    removed_count += 1
                    total_size_saved += file_size
                except Exception as e:
                    print(f"  删除失败 {file_path.name}: {e}")

    # Final statistics
    remaining_files = list(downloads_dir.rglob("*.jpg"))

    print(f"\n{'='*50}")
    print("文件名去重完成！")
    print(f"{'='*50}")
    print(f"移除文件: {removed_count}")
    print(f"节省空间: {total_size_saved / (1024*1024):.2f} MB")
    print(f"剩余文件: {len(remaining_files)}")

def download_urls(urls):
    """Download all URLs."""
    # Download files
    for url in urls:
        # 获取域名并创建对应的子文件夹
        domain = get_domain_folder(url)
        domain_folder = os.path.join("downloads", domain)
        os.makedirs(domain_folder, exist_ok=True)

        # 从 URL 提取文件名
        filename = url.split("/")[-1].split("?")[0]
        filename = get_unique_filename(domain_folder, filename)
        filepath = os.path.join(domain_folder, filename)

        print(f"Downloading {url} -> {filepath}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[SUCCESS] 下载成功: {filename}")
        except Exception as e:
            print(f"[FAILED] 下载失败: {url}\n错误: {e}")

    print("全部下载完成！")

def process_downloads(args):
    """Process downloaded files based on arguments."""
    # Remove filename-based duplicates if requested
    if args.remove_filename_duplicates:
        remove_filename_duplicates()

    # Execute perceptual deduplication unless skipped
    if not args.skip_perceptual_dedup:
        deduplicate_downloads()

# Auto-deduplication after download
def deduplicate_downloads():
    """自动去重下载的图片，使用感知哈希查找视觉重复项。"""
    if not DEDUPLICATION_AVAILABLE:
        print("去重功能不可用，请安装: pip install imagehash Pillow")
        return

    print(f"\n{'='*50}")
    print("开始自动去重...")
    print(f"{'='*50}")

    downloads_dir = "downloads"
    image_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(downloads_dir)
        for file in files
        if file.lower().endswith(('.jpg', '.jpeg'))
    ]

    if len(image_files) <= 1:
        print("文件数量不足，无需去重")
        return

    print(f"分析 {len(image_files)} 个图片文件...")

    # 1. 计算每个图片的哈希值和质量分数
    # hashes: { hash -> [(filepath, quality_score), ...] }
    hashes = defaultdict(list)
    for filepath in image_files:
        try:
            with Image.open(filepath) as img:
                file_hash = imagehash.phash(img)
                width, height = img.size
                resolution = width * height
                file_size = os.path.getsize(filepath)
                quality_score = (resolution, file_size)
                hashes[file_hash].append((filepath, quality_score))
        except Exception as e:
            print(f"无法处理文件 {filepath}: {e}")

    removed_count = 0
    total_size_saved = 0

    # 2. 查找重复项并保留质量最好的一个
    for file_hash, files_with_scores in hashes.items():
        if len(files_with_scores) > 1:
            # 按质量分数从高到低排序
            files_with_scores.sort(key=lambda item: item[1], reverse=True)
            
            keep_file_path, _ = files_with_scores[0]
            
            print(f"发现重复图片 (hash: {file_hash}):")
            print(f"  保留: {os.path.basename(keep_file_path)} (质量最高)")

            # 移除其他重复文件
            for remove_file_path, _ in files_with_scores[1:]:
                try:
                    file_size = os.path.getsize(remove_file_path)
                    os.remove(remove_file_path)
                    print(f"  移除: {os.path.basename(remove_file_path)}")
                    removed_count += 1
                    total_size_saved += file_size
                except Exception as e:
                    print(f"  删除失败 {remove_file_path}: {e}")

    # 最终统计
    remaining_files_count = len(image_files) - removed_count

    print(f"\n{'='*50}")
    print("去重完成！")
    print(f"{'='*50}")
    print(f"移除文件: {removed_count}")
    print(f"节省空间: {total_size_saved / (1024*1024):.2f} MB")
    print(f"剩余唯一图片: {remaining_files_count}")

if __name__ == "__main__":
    main()
